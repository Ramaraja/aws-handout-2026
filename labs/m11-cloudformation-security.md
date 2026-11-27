# Module 11 lab: Deploy the invoice bucket as a stack

**Time:** 35 minutes  
**Region:** ap-south-1  
**You will create:** stack `sample-invoice-bucket`  
**You will not enable:** GuardDuty, CloudTrail data events, or a customer-managed KMS key

Use the instructor’s template file `invoice-bucket.yaml`. Do not retype it from memory.

## 1. Make sure the role exists

1. In **IAM**, confirm `sample-create-order-role` exists and trusts `lambda.amazonaws.com`.
2. If it does not, create it with basic Lambda execution permissions only.

## 2. Create the stack

1. Set the region to **ap-south-1**.
2. Open **CloudFormation** → **Create stack** → upload `invoice-bucket.yaml`.
3. Stack name: `sample-invoice-bucket`.
4. Parameter `BucketName`: `sample-orders-invoices-` plus the 12-digit account id.
5. Create the stack and wait until the status is `CREATE_COMPLETE`.
6. If the status is `ROLLBACK_COMPLETE`, open **Events**, write down the resource that failed, and tell the instructor. Do not create a second stack with a different name until this one is deleted.

## 3. Check the bucket

1. Open the bucket named in the stack output.
2. Confirm versioning is on, default encryption is SSE-S3, and Block Public Access is on.
3. Open the bucket policy and confirm the principal is `sample-create-order-role` and the actions are `s3:GetObject` and `s3:PutObject`.

## 4. Read one CloudTrail event

1. Open **CloudTrail** → **Event history**.
2. Find `CreateStack` or `CreateBucket` for this lab.
3. Write down the event name, the region, and the type of principal in `userIdentity` (user or role, not the full access key).

Do not create another trail if one already exists. Do not turn on data events.

## 5. Cleanup

1. Confirm the bucket has no objects.
2. Delete the stack `sample-invoice-bucket` and wait until it is gone.
3. Confirm the bucket is gone.
4. Delete `sample-create-order-role` only if the instructor says it is unused.

## Done when

- You saw `CREATE_COMPLETE` and the four bucket settings.
- You wrote down one management event.
- The stack and the bucket are deleted.
