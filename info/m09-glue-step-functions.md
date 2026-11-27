# Glue and Step Functions

**Handout.** Region: **ap-south-1** (Mumbai).

You follow the nightly export. You create a small CSV, Glue job definition `sample-nightly-orders`, and state machine `sample-nightly-etl`. You do not start the Glue job.

## Goals

By the end of this handout you can explain:

1. How a crawler, a Data Catalog table, and a Glue job fit a small ETL path.
2. How a short Python job reads a CSV from S3 and writes a summary object.
3. How a state machine uses a choice, a success path, and a failure path.
4. Why Step Functions calls the job and the notification, instead of one Lambda doing all three.

## Glue and ETL

The nightly question is: take the orders that were exported to S3 and produce a summary another system can read. That is ETL. Extract from the CSV, transform by counting, load a summary object back to S3.

AWS Glue is the managed place Sample Orders defines that work.

- A **crawler** samples objects and infers a schema.
- The **Data Catalog** stores that schema as a database and a table. Sample’s database name is `sample_orders`. The table might be `orders_export`.
- A **job** runs the code. The job can use the catalog, or it can ignore the catalog and read a path. The script below reads a path so you are not blocked on a crawler.

A crawler is worth creating if it finishes quickly: point it at the CSV prefix, let it create `sample_orders` / `orders_export`, and open the table’s columns. If it stays in Starting, read the script instead of waiting.

Glue is not the API that accepts an order. It is a batch job. It starts, reads a file, writes a file, and stops. Between nights it should cost nothing because you do not leave workers running. A job you start by accident costs DPU-hours. Leave Run unpressed.

## Jobs and data processing

Python Shell is the smaller Glue job type and still bills if you run it. Read the script. You can paste it into a job definition and stop before Run.

```python
import csv
import os

# Shape only. Do not execute this file as a Glue job for a two-row CSV.
# A real job would use the Glue and S3 APIs to read the source bucket
# and write a summary object. The logic to follow is the three steps.

def summarize(rows):
    count = 0
    units = 0
    for row in rows:
        count += 1
        units += int(row["qty"])
    return {"orders": count, "units": units}
```

```text
orderId,sku,qty
ord-1001,BOOK-1,1
ord-1002,BOOK-2,2
```

`summarize` returns `orders` 2 and `units` 3. That is the transform. The load step, described and not run, is `PutObject` of that JSON to `summaries/nightly.json`.

Job settings to name and not tune:

- The IAM role the job assumes needs `s3:GetObject` on the CSV and `s3:PutObject` on the summary prefix. It is not `AdministratorAccess`.
- Workers and worker type decide cost. More workers are for large data. This CSV has two rows. A multi-worker Spark job is the wrong tool.
- The script lives in S3. Losing the script object is how you lose the job.

A crawler’s schema can be wrong on a tiny file. If the crawler marks `qty` as a string, the job casts it. Schema drift is a normal Glue problem. It is not fixed by failing over the region.

## Step Functions

Step Functions runs a **state machine**. An **execution** is one run, with input JSON and a history of states. You can see which state failed. That is the reason to use it instead of a long function with nested try blocks.

Sample’s machine is `sample-nightly-etl`. The practice machine uses states that finish immediately:

| State | Type | What it shows |
| --- | --- | --- |
| `CheckInput` | Choice | If `$.status` equals `ok`, go to `Summarize`. Otherwise go to `FailExport`. |
| `Summarize` | Pass | Stands in for the Glue job. The result field says the summary would be written. |
| `Notify` | Pass | Stands in for `sns:Publish`. |
| `FailExport` | Fail | A chosen failure with a named error. |
| `Succeeded` | Succeed | The end of the good path. |

A production machine replaces the Pass states with a Glue `StartJobRun` sync integration and an SNS publish. The shape of the graph stays. Pass states keep a missing Glue run from billing you and from taking minutes.

Error handling in the definition:

- **Retry** on a task state, with a limited number of attempts and a backoff, for a transient Glue throttle.
- **Catch** sends the execution to `FailExport` instead of ending as an unhandled failure.
- **Choice** branches on input. That is what this machine uses for `status`.

Happy-path input:

```json
{"status": "ok", "exportKey": "exports/orders.csv"}
```

Failure-path input: `{"status": "fail"}`.

## How Glue, Lambda, and Step Functions fit

`sample-create-order` is still the short API function. It should not read the whole export.

A reasonable nightly wiring:

1. Something starts the state machine on a schedule. EventBridge Scheduler is the usual trigger. You can also start one execution yourself.
2. The machine starts the Glue job and waits.
3. On success it publishes a small event. A dedicated topic is cleaner than reusing `order-events`, because order subscribers should ignore export messages. This example does not publish.
4. On failure the machine ends in `FailExport`. The metric `ExecutionsFailed` in the Step Functions namespace is the alarm to add later.

Lambda still has a place inside the machine for a short step, such as validating the export key before Glue starts. The Choice state is that validation, without a function.

One Lambda that polls Glue in a loop for an hour pays for the wait and hits the 15-minute timeout. The state machine is what waits.

## In the console

### 1. Put the CSV in S3

1. Region **ap-south-1**.
2. Use a bucket you will delete, named `sample-orders-exports-ACCOUNTID`, with Block Public Access on.
3. Upload `exports/orders.csv` with the two-row CSV above.

### 2. Show the Glue job without running it

1. **Glue** → **ETL jobs** → create a job with a script you author, or a Python Shell job if that is what the console offers.
2. Name it `sample-nightly-orders`.
3. Paste the summarize logic into the script editor. Point at source path `exports/orders.csv` and destination `summaries/nightly.json`.
4. The role field stays narrow. Do not attach `AdministratorAccess`.
5. Save if the console requires it to show the script. **Do not run the job.** If Save and Run are the same button, cancel the run immediately.

Optional, only if it returns in a couple of minutes: a crawler `sample-orders-crawler` on that prefix, database `sample_orders`. Skip it if it sits in Starting.

### 3. Create and run the state machine

1. **Step Functions** → **Create state machine**.
2. Name `sample-nightly-etl`. Type: Standard.
3. Use the definition below. Create a new role that Step Functions offers for CloudWatch Logs if asked. The definition does not call other services, so the role stays narrow.

```json
{
  "Comment": "Sample Orders nightly export. Pass states stand in for Glue and SNS.",
  "StartAt": "CheckInput",
  "States": {
    "CheckInput": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.status",
          "StringEquals": "ok",
          "Next": "Summarize"
        }
      ],
      "Default": "FailExport"
    },
    "Summarize": {
      "Type": "Pass",
      "Result": {"orders": 2, "units": 3, "wrote": "summaries/nightly.json"},
      "ResultPath": "$.summary",
      "Next": "Notify"
    },
    "Notify": {
      "Type": "Pass",
      "Result": {"published": false, "reason": "Pass stands in for SNS"},
      "ResultPath": "$.notify",
      "Next": "Succeeded"
    },
    "Succeeded": {"Type": "Succeed"},
    "FailExport": {
      "Type": "Fail",
      "Error": "ExportRejected",
      "Cause": "status was not ok"
    }
  }
}
```

4. Start an execution with `{"status":"ok","exportKey":"exports/orders.csv"}`. The graph should end in Succeeded, and the output should contain `orders` 2.
5. Start a second execution with `{"status":"fail"}`. It should end in `FailExport` with `ExportRejected`.

**If the Choice throws a path error:** the input did not contain `status`. Fix the input. Keep the branch.

## When you are done

1. Delete the state machine `sample-nightly-etl`. Stop any running execution first.
2. Delete the Glue job `sample-nightly-orders` if it was saved. Confirm **no job runs** are in Running.
3. Delete the crawler and the catalog database if you created them.
4. Empty and delete `sample-orders-exports-ACCOUNTID`.
5. Delete the Step Functions role if the console created one and it is unused.

The check is two executions with two different endings, and a note that `Summarize` stands in for `sample-nightly-orders`. Do not press Run on the Glue job. Do not add a distributed map over a large S3 listing.

## What this costs

Step Functions Standard has a free tier that covers a few short executions. Glue bills a casual Run. Check the Glue job runs page before you leave. It must be empty.
