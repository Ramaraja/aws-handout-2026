# CloudFormation, CloudTrail, and security controls

**Handout.** Region: **ap-south-1** (Mumbai).

You describe the invoice bucket as code and read who created it. You create stack `sample-invoice-bucket` and role `sample-create-order-role` if it is missing. Create a trail only if the account has none.

## Goals

By the end of this handout you can explain:

1. A template’s parameters, resources, and outputs, and what a stack and a change set are.
2. How to create the invoice bucket from a template and delete the stack, including what rollback does after a failed create.
3. How to read one CloudTrail management event for that create, and what a trail adds beyond event history.
4. How a preventive control differs from a detective one. GuardDuty is the managed finding service. You can name it without enabling it.

## CloudFormation

A **template** is a text file that describes resources. A **stack** is the live set CloudFormation created from one template, in one region, with a name. Sample’s stack is `sample-invoice-bucket` in `ap-south-1`. Deleting the stack deletes the bucket the template owns. Deleting the bucket in the S3 console and leaving the stack makes the next update fail. The stack is the handle.

Three sections to be able to point at:

- **Parameters** are inputs. `BucketName` is a parameter because bucket names are global and must include the account id.
- **Resources** are the bucket and the bucket policy. The bucket enables versioning, blocks public access, and sets SSE-S3. The policy is the Allow for `sample-create-order-role`.
- **Outputs** print the bucket name after the stack is created.

`AWS::AccountId` is a pseudo-parameter. The policy ARN is built from it. The role still has to exist. This template does not create the role. The role is a separate identity. Putting the bucket and every IAM principal into one template makes stacks hard to delete.

A **change set** is a preview. You ask CloudFormation what an updated template would add, change, or replace, and you execute it only after you read the list. Replacement of a bucket means data migration, not an in-place edit. Adding a tag is a safe change to preview. You can open a change set and delete it without executing it. Do not update a stack you care about without reading the change set.

**Rollback:** if resource creation fails, CloudFormation deletes what it already created for a new stack and lands in `ROLLBACK_COMPLETE`. A common cause is a bucket policy that names a role that does not exist. Create the role and create the stack again. There should be no bucket left after rollback. Check S3 anyway.

This stack is the written form of the S3 console clicks. The Serverless Framework file for the API is the same idea. You can create the resources in the console and still read the template.

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: Sample Orders invoice bucket
Parameters:
  BucketName:
    Type: String
    Description: Globally unique name, sample-orders-invoices plus the account id
Resources:
  InvoiceBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Ref BucketName
      VersioningConfiguration:
        Status: Enabled
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
  InvoiceBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref InvoiceBucket
      PolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Sid: AllowCreateOrderRole
            Effect: Allow
            Principal:
              AWS: !Sub "arn:aws:iam::${AWS::AccountId}:role/sample-create-order-role"
            Action:
              - s3:GetObject
              - s3:PutObject
            Resource: !Sub "${InvoiceBucket.Arn}/*"
Outputs:
  BucketName:
    Description: Invoice bucket
    Value: !Ref InvoiceBucket
```

## CloudTrail

CloudTrail records API calls. A **management event** is a control-plane call: `CreateStack`, `CreateBucket`, `DeleteStack`, `PutBucketPolicy`. **Event history** in the console shows recent management events even when you have not created a trail. That is enough to investigate this deploy.

A **trail** delivers those events to S3 (and optionally to CloudWatch Logs) and keeps them beyond the event-history window. The first trail that records management events in the account is inside the free tier. A second trail that records the same management events is not. Data events, such as every `GetObject`, are a separate setting and they cost money. Leave data events off for this exercise.

Read one event. Find `CreateStack` or `CreateBucket` and use these fields:

| Field | What it answers |
| --- | --- |
| `eventTime` | When |
| `eventName` | Which API |
| `eventSource` | Which service |
| `awsRegion` | Should be `ap-south-1` |
| `userIdentity` | Who. This should be your IAM user or role. |
| `sourceIPAddress` | Where from |
| `requestParameters` | The stack name or bucket name. It should not contain a password. This template does not pass one. |

If the identity on the event is the root user, switch later work to an IAM user or role.

A trail is a detective control. It does not stop a bad call. It tells you the call happened.

## Preventive and detective controls

**Preventive** controls stop an action:

- MFA on the root user.
- A role with basic execution plus the two S3 actions, not `AdministratorAccess`.
- The bucket’s Block Public Access and the bucket policy.
- Security groups that do not open Aurora or the packing task to the world.

**Detective** controls tell you after, or while, something is wrong:

- CloudTrail for who called which API.
- The alarm `sample-create-order-errors` and a queue-age alarm.
- A failed state-machine execution.

SSE-S3 encrypts the object with a key S3 manages. You do not write a key policy. **SSE-KMS** with a customer-managed key adds a **key policy**: who may use the key to decrypt. That is the right control when you must revoke decrypt permission without rewriting every IAM user. This exercise does not create that key. It adds policy surface, cost, and a lock-out risk for a one-line invoice. SSE-S3 still encrypts the object.

**GuardDuty** reads CloudTrail and other telemetry and raises findings, such as an API call from an unusual place. It can be the right production choice and it is a paid service after the trial. You can name it without enabling it.

The invoice stack should be private, logged, and small enough that you can explain every permission.

## In the console

### 1. Create the role if it is missing

1. IAM → create `sample-create-order-role` for the Lambda service with `AWSLambdaBasicExecutionRole` only.
2. If the role already exists, do not attach an S3 admin policy.

### 2. Create the stack

1. Region **ap-south-1**. Save the template as `invoice-bucket.yaml`.
2. **CloudFormation** → **Create stack** → with new resources → upload the file.
3. Stack name `sample-invoice-bucket`.
4. Parameter `BucketName`: `sample-orders-invoices-ACCOUNTID`.
5. This template creates a bucket policy, not a role. If the console asks you to acknowledge a capability, read it before you tick it.
6. Create the stack. Wait for `CREATE_COMPLETE`.

**Expected:** stack complete. S3 shows the bucket. Versioning is on. Default encryption is SSE-S3. Block Public Access is on. The bucket policy names the role.

**If the stack rolls back:** open Events. The failed resource is usually `InvoiceBucketPolicy` because the role is missing or the name is wrong. Confirm there is no leftover bucket. Create the role. Create the stack again.

**If the bucket name is taken:** pass a parameter that matches an unused name with the account id in it. Leave the template unchanged.

### 3. Read one event

1. **CloudTrail** → **Event history**.
2. Filter by event name `CreateStack` or resource name `sample-invoice-bucket`.
3. Open the event and read identity, time, region, and request parameters.

**Expected:** one management event for this create. Region `ap-south-1`.

**If the event is missing:** wait a minute and refresh. Event history is not instant. Do not create a second trail to duplicate the same event.

### 4. Trail, only if the account has zero trails

1. If a trail already exists, open it, confirm it logs management events, and do not create another.
2. If none exists, event history already proved the point. Prefer that over a new log bucket. A trail’s log bucket is another resource to delete. One management trail named `sample-management-trail` is enough if you want events kept beyond the history window. Do not record data events.

### 5. Optional change set

Prepare an update that adds a tag `Project=sample` on the bucket, create a change set, confirm it shows a modify on the bucket, and delete the change set without executing it. The bucket stays as first created.

## When you are done

1. Confirm the invoice bucket is empty. If you uploaded an object, empty all versions.
2. Delete the stack `sample-invoice-bucket`. Wait until it is gone. The bucket should disappear with it.
3. If you created a trail and a log bucket for this exercise, delete the trail and then the log bucket. If the account already had a trail, leave that trail.
4. Delete `sample-create-order-role` if nothing else in the account uses it.
5. Confirm S3 has no `sample-orders-invoices-ACCOUNTID` bucket.

One stack is enough. Do not enable GuardDuty, data events, or a customer-managed KMS key. A rollback is useful if you read the event and then delete the stack. Do not leave a stack in `ROLLBACK_COMPLETE`.

## What this costs

An empty bucket is negligible. A second CloudTrail trail or data events are the charges to avoid. Delete the stack when you are finished.
