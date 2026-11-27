# CloudWatch monitoring and observability

**Handout.** Region: **ap-south-1** (Mumbai).

You watch the order path with a metric, a log, and an alarm. You create function `sample-create-order` as a log source, dashboard `sample-orders`, and alarm `sample-create-order-errors`.

## Goals

By the end of this handout you can explain:

1. What a metric, a dimension, a log event, an alarm, and a dashboard each answer.
2. Which Sample Orders metrics matter for Lambda, API Gateway, SQS, and Aurora, and how to attach an alarm to one of them.
3. How to walk from a symptom to a metric to a log line before changing code.
4. What X-Ray would add, and why the metric-then-log path still matters.

## Monitoring fundamentals

CloudWatch is the place Sample Orders looks before it changes code.

| Question | CloudWatch object |
| --- | --- |
| How many, how long, how full? | A **metric** |
| Which resource is this number about? | A **dimension**, such as `FunctionName` |
| What did the code say when it failed? | A **log event** in a log group |
| Who should be told, and when? | An **alarm** on a metric |
| Can an operator see the set together? | A **dashboard** |

A metric is a time series published by a service or by your code. `Errors` for Lambda is already published. You do not instrument it. A custom metric is how you would publish `OrdersAccepted`. This example does not call `PutMetricData`.

A dimension filters the series. `Errors` for all functions is a different series from `Errors` where `FunctionName` is `sample-create-order`. An alarm without that dimension pages you for someone else’s function.

Logs are not metrics. A log line is cheap to read and a poor thing to graph until you turn a count of matches into a **metric filter**. You do not need a filter to start. It exists so “count the word Exception” does not stay a manual search.

Namespaces:

- `AWS/Lambda`
- `AWS/ApiGateway`
- `AWS/SQS`
- `AWS/RDS` for Aurora
- `AWS/ECS` when the packing service is running

## Metrics, logs, alarms, and dashboards

Lambda, for `sample-create-order`:

| Metric | Reading |
| --- | --- |
| `Invocations` | The function was called. It does not mean the order was correct. |
| `Errors` | The function threw, or the runtime failed. A handled 400 you return as `statusCode` is not this metric. |
| `Duration` | How long the handler ran. A timeout is an error and a duration near the timeout setting. |
| `Throttles` | The account or the reserved concurrency rejected the invoke. |

API Gateway HTTP APIs publish to `AWS/ApiGateway`. `5xx` means the integration failed from the client’s point of view. `4xx` is often a route or auth miss. A 500 with Lambda `Errors` at zero may be API Gateway itself, including a missing invoke permission.

SQS:

| Metric | Reading |
| --- | --- |
| `ApproximateNumberOfMessagesVisible` | Work waiting. A growing number means consumers are behind or broken. |
| `ApproximateAgeOfOldestMessage` | How long the oldest message has waited. Age is the better alarm. A queue can have one message that is an hour old. |
| Visible messages on `inventory-dlq` | Poison messages. Any number above zero is a defect, not a backlog to scale out blindly. |

Aurora, namespace `AWS/RDS`, dimension `DBClusterIdentifier` = `sample-orders-db`:

- `CPUUtilization`
- `DatabaseConnections`

Alarms need a period, a statistic, a threshold, and a missing-data choice. The alarm in this example:

- Name: `sample-create-order-errors`
- Metric: `AWS/Lambda` `Errors`, dimension `FunctionName` = `sample-create-order`
- Statistic: Sum, period 1 minute
- Threshold: greater than or equal to 1
- Missing data: treat as not breaching, so an idle function does not page

The alarm state is OK, ALARM, or INSUFFICIENT_DATA. Sending to an email requires an SNS topic. The threshold is the point to learn. You can create the alarm and read the state without a notification topic.

A dashboard named `sample-orders` holds widgets for Lambda invocations, SQS oldest-message age for `inventory-queue`, Aurora CPU, and the log group `/aws/lambda/sample-create-order`. An empty graph still records the metric you intend to watch after the resource is gone.

## What to watch

Infrastructure metrics tell you the platform moved. Application logs tell you which order it was.

For a place-order failure, look in this order:

1. API Gateway `5xx` and count, so you know the client’s symptom is real.
2. Lambda `Errors` and `Duration` for `sample-create-order`.
3. The log stream for that function, around the same minute. You want the `orderId` and the exception text.
4. If the log says the database timed out, Aurora `DatabaseConnections` and `CPUUtilization`.
5. If the log says the publish succeeded and inventory is wrong an hour later, SQS age on `inventory-queue` and depth on `inventory-dlq`.

X-Ray can stitch those hops into one trace id. Start with the metric, then the log. Tracing is optional.

Logs can contain customer data. The stub prints an order id. Do not print a card number or the database password. CloudWatch Logs retention defaults to never expire. Set a short retention, or delete the log group when you are finished.

## A root-cause path

**Symptom:** the client receives HTTP 500 from `POST /orders`.

**Metric:** `AWS/Lambda` `Errors` for `sample-create-order` increased in the same minute. API Gateway `5xx` increased. Aurora CPU did not.

**Log:** the stream shows the exception, for example `KeyError: sku`. The request id in the Lambda log matches the API request id if you printed it.

**Cause:** the handler assumed a field the client did not send. The fix is code or validation, not a larger Fargate task and not a Multi-AZ failover.

A second story, described rather than built:

**Symptom:** orders succeed and inventory is stale.

**Metric:** `ApproximateAgeOfOldestMessage` on `inventory-queue` is climbing. Lambda `Errors` for `sample-inventory-worker` may also be climbing.

**Log:** the worker throws on a bad payload.

**Cause:** poison messages. After the receive count, they should sit on `inventory-dlq`. If age climbs and the DLQ is empty, the worker is slow or the visibility timeout is too short and messages are spinning.

The metric either moved or it did not. If it did not move, you are looking at the wrong resource.

## In the console

### 1. Create a function you can break on purpose

1. Region **ap-south-1**. Create Lambda `sample-create-order`, Python 3.12, basic execution role `sample-create-order-role`.
2. Deploy:

```python
def lambda_handler(event, context):
    print("accepted", event)
    return {"statusCode": 201, "body": "ok"}
```

3. Invoke once with the test button and any JSON object. Confirm a log line in `/aws/lambda/sample-create-order`.

### 2. Build the dashboard

1. **CloudWatch** → **Dashboards** → **Create dashboard** → name `sample-orders`.
2. Add a line widget. Namespace `AWS/Lambda`, metric `Invocations`, dimension `FunctionName` = `sample-create-order`, statistic Sum, period 1 minute.
3. Add a line widget. Namespace `AWS/SQS`, metric `ApproximateAgeOfOldestMessage`, dimension `QueueName` = `inventory-queue`. If the queue does not exist, keep the metric name in your notes. Do not recreate the whole queue stack to fill one graph.
4. Add a line widget. Namespace `AWS/RDS`, metric `CPUUtilization`, dimension `DBClusterIdentifier` = `sample-orders-db`, only if the cluster still exists. If it does not, record the metric name and skip the widget.
5. Save the dashboard.

### 3. Create the alarm and trip it

1. **CloudWatch** → **Alarms** → **Create alarm**.
2. Metric: Lambda `Errors` for `FunctionName` `sample-create-order`. Sum, 1 minute, threshold **>= 1**. Missing data: not breaching.
3. Name `sample-create-order-errors`. A notification topic is optional.
4. Change the function to raise:

```python
def lambda_handler(event, context):
    raise RuntimeError("forced error")
```

5. Deploy and invoke once.
6. Read the log line with `RuntimeError`. Watch the alarm move to ALARM. Metric delay can be one or two minutes. Invoke once. Do not invoke in a loop.

**Expected:** one error in the log, then the alarm in ALARM.

**If the alarm stays OK:** the dimension does not match the function name, or the period has not closed. Open the metric graph before you rewrite the function.

You are about to delete the function. Leaving the raise in place is fine.

## When you are done

1. Delete alarm `sample-create-order-errors`.
2. Delete dashboard `sample-orders`.
3. Delete function `sample-create-order` and role `sample-create-order-role`.
4. Delete log group `/aws/lambda/sample-create-order`.

Record the metric name, the dimension, and the log sentence. Do not enable X-Ray, Container Insights, or a high-resolution custom metric. A one-minute period is enough.

## What this costs

Dashboards and a standard alarm at this count are inexpensive. The risk is a log group that never expires after a function logs in a loop. Invoke once. Delete the function and the log group.
