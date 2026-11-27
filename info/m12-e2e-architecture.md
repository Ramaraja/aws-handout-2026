# End-to-end architecture

**Handout.** Region: **ap-south-1** (Mumbai).

You trace one order across the pieces you have already used. You create nothing and add no new service.

## Goals

By the end of this handout you can explain:

1. The path of `POST /orders` across the API, the function, the database, the topic, the queues, and the invoice object.
2. The identity, the network rule, the alarm, and the recovery control for each data store.
3. The defects in a weak copy of the same architecture, and which control fixes each one.
4. One recovery choice for Aurora and one for S3, using only the controls already described.

## The path of one order

Use a single order, `ord-1001`, for `BOOK-1`, quantity 1.

1. The client calls `POST /orders` on the HTTP API `sample-orders-api` in `ap-south-1`. The stage is `$default`. There is no authorizer. The URL is only as private as the network and the auth you add later.
2. API Gateway invokes `sample-create-order`. The function’s execution role is `sample-create-order-role`. API Gateway’s permission to invoke is a resource policy on the function, not that role.
3. The function writes the row to database `orders` on Aurora cluster `sample-orders-db`, using the **writer endpoint**. The security group `sample-aurora-sg` allows 3306 from the function’s security group. The function has to be in the VPC for that path to exist. The first stub was not in a VPC. The end-state story puts it in private subnets, with Aurora’s security group trusting it. A gateway or interface endpoint is the way out to other AWS APIs. A NAT gateway is the expensive alternative. You do not need to create the endpoint to state that design.
4. The function puts `invoices/ord-1001.txt` in `sample-orders-invoices-ACCOUNTID`. The bucket policy allows the role `s3:PutObject`. Block Public Access is on. Versioning is on. Encryption is SSE-S3. The stack `sample-invoice-bucket` is how that bucket is created again.
5. The function publishes `{"orderId":"ord-1001","sku":"BOOK-1","qty":1}` to `order-events`.
6. SNS delivers a copy to `inventory-queue` and `notify-queue`. `inventory-queue` has a redrive policy to `inventory-dlq` after 3 receives. Visibility timeout is 30 seconds, longer than the worker.
7. `sample-inventory-worker` consumes the inventory queue. A duplicate `orderId` must not decrement stock twice.
8. `sample-packing` on Fargate reads rows that are ready to ship. Its task role, not the image, is what may call AWS. The first packing task left that role empty and used a public image as a stand-in. The end state does not expose port 80.

The nightly path sits beside this, not inside the POST. `sample-nightly-etl` runs `sample-nightly-orders` against a CSV in S3. Pass states can stand in for the job while you learn the graph. The production shape is the same graph with a real job.

## Security, monitoring, and availability

| Concern | Sound Sample Orders | Where it is described |
| --- | --- | --- |
| Root | MFA, and root unused for ordinary work | Account fundamentals |
| Function identity | `sample-create-order-role`, logs plus the specific S3 and SNS actions | Networking, Lambda, S3 |
| Database network | No public access. 3306 from the application security group only | Networking and Aurora |
| Packing network | No inbound on `sample-fargate-sg` | Fargate |
| Invoice bucket | Block Public Access, versioning, SSE-S3, stack `sample-invoice-bucket` | S3 and CloudFormation |
| Poison messages | `inventory-dlq` | SQS and SNS |
| API failures | Alarm `sample-create-order-errors` on Lambda `Errors` | CloudWatch |
| Stuck inventory | Alarm on `ApproximateAgeOfOldestMessage` | CloudWatch |
| Who changed the stack | CloudTrail management events | CloudTrail |
| Zone loss | Aurora Multi-AZ failover, same writer endpoint | Aurora and disaster recovery |
| Region loss | Redeploy functions and jobs. CRR for invoices. Cross-region replica plus backups for Aurora. Active-active is not the default | Disaster recovery |

Availability of the HTTP API inside one region is mostly AWS’s problem for API Gateway and Lambda. Availability of the **row** is the Aurora failover story. Availability of the **invoice after a region loss** is the replication story. Using AWS does not by itself make the design multi-region.

## A weak design of the same system

Same names, built badly:

- Aurora `sample-orders-db` has public access on, and `sample-aurora-sg` allows 3306 from `0.0.0.0/0`.
- The invoice bucket has Block Public Access off and a policy with `Principal: *` on `s3:GetObject`.
- `inventory-queue` has no dead-letter queue. The worker throws on bad JSON and the message returns forever.
- Nobody built `sample-create-order-errors` or a queue-age alarm.
- CloudTrail trails were deleted, and nobody reads event history.
- The design notes say “one Availability Zone is enough” for the database and “versioning is our regional DR.”

| Flaw | Repair | Leave this alone |
| --- | --- | --- |
| Public database | Public access off. Inbound 3306 from `sample-lambda-sg` or `sample-fargate-sg` only | A NAT gateway |
| Public bucket | Block Public Access on. Remove `Principal *`. Allow the role `GetObject` and `PutObject` | A second unencrypted bucket |
| No DLQ | `inventory-dlq`, max receives 3 | A larger Lambda memory setting as the only change |
| No alarm | `sample-create-order-errors`, and age on `inventory-queue` | X-Ray as a substitute for an alarm |
| No trail | Event history for the short term, one management trail if the account has none | Data events on every `GetObject` |
| Single-zone story | Aurora subnet group in two zones and failover for a zone loss. Versioning for a bad upload. CRR and a cross-region database replica when the requirement is a lost region | Calling Multi-AZ a multi-region design |

The bucket and its policy belong to stack `sample-invoice-bucket`. Keep the database in its own change boundary so a bucket update cannot replace the database. One giant stack increases blast radius.

You can name GuardDuty as a later detective control. You do not need to turn it on to review this design. CloudFront, a second account, and a NAT gateway are not required to repair the six flaws.

## Walk the design

1. Write the eight steps for `ord-1001`.
2. Write the six flaws beside them.
3. Repair the public database first. The security group source is a security group, not `0.0.0.0/0`.
4. Repair the other five from the table. That list is your worksheet.

A replica is not a backup. A fast replica copies a bad delete. Backups and point-in-time restore are what let you return to a time before that delete.

## When you are done

Check S3, CloudFormation, RDS, ECS, and Lambda for `sample-` names. Delete anything that is not the budget `sample-orders-training`.

## What this costs

This review creates nothing. The closing check of the console is part of the notes. Delete any `sample-` resource you find, except the budget.
