# Module 4 lab: Fan-out from order-events

**Time:** 35 minutes  
**Region:** ap-south-1  
**You will create:** `inventory-dlq`, `inventory-queue`, `notify-queue`, `order-events`, and `sample-inventory-worker`

## 1. Create the queues

1. Set the region to **ap-south-1**.
2. Open **SQS** and create a standard queue named `inventory-dlq`. Leave the defaults.
3. Create a standard queue named `inventory-queue`.
   - Visibility timeout: **30** seconds.
   - Receive message wait time: **20** seconds.
   - Dead-letter queue: `inventory-dlq`, maximum receives **3**.
4. Create a standard queue named `notify-queue` with the same visibility timeout and wait time. Do not attach a dead-letter queue.

## 2. Create the topic and subscriptions

1. Open **SNS** → **Topics** → create a standard topic named `order-events`.
2. Create a subscription. Protocol **Amazon SQS**. Choose `inventory-queue`. Leave raw message delivery off.
3. Create a second subscription to `notify-queue`.
4. Confirm both subscriptions show as confirmed.

## 3. Create the worker

1. Open **Lambda** and create a function named `sample-inventory-worker`, runtime **Python 3.12**.
2. Let the console create a role that can write logs and read from `inventory-queue` when you add the trigger.
3. Deploy this code:

```python
def lambda_handler(event, context):
    for record in event.get("Records", []):
        print(record.get("body"))
    return {"processed": len(event.get("Records", []))}
```

4. Add a trigger from **SQS** queue `inventory-queue`, batch size **1**.
5. Set the function timeout to **3** seconds.

## 4. Publish one order event

1. On the topic `order-events`, publish this message body:

```json
{"orderId":"ord-1001","sku":"BOOK-1","qty":1}
```

2. Poll `notify-queue` in the SQS console. You should see one message. Open it and find your JSON inside the SNS envelope.
3. Open the latest CloudWatch log stream for `sample-inventory-worker`. You should see the same event.
4. Confirm `inventory-dlq` has no messages.

Use your own `orderId` if someone else already published `ord-1001`.

## 5. Cleanup

1. Delete the function `sample-inventory-worker` and its role.
2. Delete the subscriptions, then the topic `order-events`.
3. Delete `inventory-queue` and `notify-queue`, then `inventory-dlq`.

## Done when

- One publish produced a message on `notify-queue` and a log line from `sample-inventory-worker`.
- The dead-letter queue was empty after that successful run.
- The topic, the queues, the function, and the role are deleted.
