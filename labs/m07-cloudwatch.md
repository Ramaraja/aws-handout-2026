# Module 7 lab: One dashboard and one alarm

**Time:** 35 minutes  
**Region:** ap-south-1  
**You will create:** `sample-create-order`, dashboard `sample-orders`, alarm `sample-create-order-errors`

If the instructor is driving a shared console, write the notes in each step while they click. Do not create a second alarm with the same name.

## 1. Create a function that can log

1. Set the region to **ap-south-1**.
2. Create a Python 3.12 function named `sample-create-order` with a basic execution role named `sample-create-order-role`.
3. Deploy:

```python
def lambda_handler(event, context):
    print("accepted", event)
    return {"statusCode": 201, "body": "ok"}
```

4. Invoke it once from the Test tab. Open `/aws/lambda/sample-create-order` and confirm a log line that contains `accepted`.

## 2. Create the dashboard

1. Open **CloudWatch** → **Dashboards** → create `sample-orders`.
2. Add a line widget for `AWS/Lambda` metric `Invocations`, dimension `FunctionName` = `sample-create-order`, statistic Sum, period 1 minute.
3. Add a line widget for `AWS/SQS` metric `ApproximateAgeOfOldestMessage` and dimension `QueueName` = `inventory-queue` if that series exists. If the queue was deleted, write that metric name on your notes and skip the widget.
4. If cluster `sample-orders-db` still exists, add `AWS/RDS` metric `CPUUtilization` for that cluster. If it does not, write the metric name in your notes.
5. Save the dashboard.

## 3. Create the alarm and cause one error

1. Create alarm `sample-create-order-errors`.
2. Metric: Lambda `Errors` for function `sample-create-order`.
3. Statistic Sum, period 1 minute, threshold greater than or equal to **1**.
4. Missing data: treat as **not breaching**.
5. Replace the function code with:

```python
def lambda_handler(event, context):
    raise RuntimeError("forced for the alarm lab")
```

6. Deploy and invoke **once**.
7. In the log stream, find `RuntimeError`.
8. Watch the alarm. It can take a minute to enter **ALARM**.

## 4. Write the path

On paper, in order: the client symptom you would have seen if this function sat behind the API, the metric that moved, and the log text that explains it.

## 5. Cleanup

1. Delete the alarm `sample-create-order-errors`.
2. Delete the dashboard `sample-orders`.
3. Delete the function and the role.
4. Delete the log group `/aws/lambda/sample-create-order`.

## Done when

- You saw one error log line and an alarm aimed at that function’s `Errors` metric.
- The dashboard or your notes name the SQS age metric and the Aurora CPU metric.
- The alarm, dashboard, function, role, and log group are deleted.
