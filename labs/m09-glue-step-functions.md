# Module 9 lab: A state machine that stands in for the nightly job

**Time:** 35 minutes  
**Region:** ap-south-1  
**You will create:** a small CSV bucket and the state machine `sample-nightly-etl`  
**You will not do:** run a Glue job

## 1. Put a CSV in S3

1. Set the region to **ap-south-1**.
2. Create a bucket `sample-orders-exports-` plus the account id. Block all public access.
3. Upload `exports/orders.csv` containing:

```text
orderId,sku,qty
ord-1001,BOOK-1,1
ord-1002,BOOK-2,2
```

## 2. Look at the job shape

On the instructor’s screen, find the Glue job name `sample-nightly-orders` and the idea of the script: read that CSV, count orders and units, write `summaries/nightly.json`.

Write down the counts you expect: orders and units.

Do not start a Glue job. If you are in the Glue console, leave it without pressing Run.

## 3. Create the state machine

1. Open **Step Functions** and create a Standard state machine named `sample-nightly-etl`.
2. Paste the definition the instructor shows. The states are `CheckInput`, `Summarize`, `Notify`, `Succeeded`, and `FailExport`.
3. Accept a role that only lets the state machine write its own logs.

## 4. Run it twice

1. Start an execution with this input:

```json
{"status":"ok","exportKey":"exports/orders.csv"}
```

2. Confirm the execution succeeds and the output includes the summary the instructor’s Pass state added.
3. Start a second execution with:

```json
{"status":"fail"}
```

4. Confirm this execution fails with `ExportRejected`.

## 5. Write one sentence

`Summarize` is a Pass state in the lab. Name the Glue job it stands in for, and name the S3 key of the CSV.

## 6. Cleanup

1. Delete the state machine `sample-nightly-etl`.
2. Delete the Glue job, crawler, or catalog database if one was saved. Confirm there is no running job.
3. Empty and delete the exports bucket.

## Done when

- One execution succeeded and one failed on purpose.
- You did not start a Glue job.
- The state machine and the exports bucket are gone.
