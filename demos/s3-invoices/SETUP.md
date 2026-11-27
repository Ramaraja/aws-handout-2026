# Create the invoice bucket in the console

Do this in the AWS console. Region: **ap-south-1**. Stay in Mumbai for every step. Do not create a bucket in Singapore and do not add a replication rule.

You will create:

1. Bucket `sample-orders-invoices-` plus your account id
2. Two versions of the object `invoice.txt`
3. A lifecycle rule and a bucket policy for `sample-create-order-role`

The invoice is an object. It is not the order row.

## 1. Set the region and copy the account id

1. Sign in to the training account.
2. In the top bar, set the region selector to **Asia Pacific (Mumbai) ap-south-1**.
3. Search for **IAM** and open the dashboard.
4. Copy the **Account ID**. It is 12 digits. Write it down as `ACCOUNTID`. You will use it in the bucket name and in the bucket policy.

## 2. Create the bucket

1. Search for **S3** and open it.
2. Choose **Create bucket**.
3. Bucket name: `sample-orders-invoices-ACCOUNTID`. Example: if the account id is `123456789012`, the name is `sample-orders-invoices-123456789012`.
4. AWS Region: **Asia Pacific (Mumbai) ap-south-1**.
5. Object Ownership: **Bucket owner enforced** (ACLs disabled). Leave this if it is already the default.
6. Block Public Access settings for this bucket: leave **Block all public access** on. All four checkboxes stay selected.
7. Bucket Versioning: **Enable**.
8. Default encryption: **Server-side encryption with Amazon S3 managed keys (SSE-S3)**. Encryption type SSE-S3, bucket key not required.
9. Do not enable replication.
10. Choose **Create bucket**.

If the name is already taken, you mistyped the account id or an old bucket is still there. Do not pick a different public name. Empty and delete the old one, or fix the suffix, then create it again.

Open the bucket and confirm three settings before you upload:

- **Properties** shows Bucket Versioning **Enabled**.
- **Properties** shows Default encryption **SSE-S3** (AES-256).
- **Permissions** shows Block Public Access **On**.

## 3. Upload two versions of the same key

1. On your computer, create a text file named `invoice.txt`. The file contains one line:

```text
version one
```

2. In the bucket, choose **Upload**, add `invoice.txt`, and upload it. Leave the other upload options at their defaults. The bucket encryption applies because you did not choose a different key.
3. Change the file on your computer so the line is:

```text
version two
```

4. Upload `invoice.txt` again to the same bucket. The key must stay `invoice.txt`. Do not rename it to `invoice-v2.txt`.

Expected: the object list shows one key, `invoice.txt`.

## 4. Read both versions

1. Open the object `invoice.txt`.
2. Choose **Versions** (or the versions toggle on the object list).
3. Confirm two version ids. The current version is the one marked latest. Download or open it and confirm the body is `version two`.
4. Select the older version id, not the latest, and download it. Confirm the body is `version one`.

That older copy is why a bad overwrite in this bucket has a short recovery. You did not lose `version one`.

A delete of `invoice.txt` that does not name a version id would add a **delete marker** and make a normal GET look empty. The older bytes would still be there until you delete that version id or a lifecycle rule expires it. Do not delete the object in this demo.

## 5. Add the lifecycle rule

1. Open the bucket **Management** tab.
2. Under **Lifecycle rules**, choose **Create lifecycle rule**.
3. Rule name: `expire-noncurrent-invoices`.
4. Choose to apply the rule to the whole bucket.
5. Rule action: **Permanently delete noncurrent versions of objects**.
6. Days after objects become noncurrent: **30**.
7. Do not add a transition to another storage class. Do not expire current versions.
8. Create the rule.

The rule does not run during class. It only records that noncurrent invoice versions should not live forever. An expiration rule that is too short is how you destroy the copy you meant to keep. Read the 30-day value before you save.

## 6. Add the bucket policy

The policy grants `sample-create-order-role` permission to read and write objects in this bucket. The role must exist before the policy will save.

### Create the role if it is missing

1. Open **IAM**, then **Roles**.
2. If `sample-create-order-role` is already listed, do not create another and do not add an S3 admin policy to it.
3. If it is missing, choose **Create role**.
4. Trusted entity type: **AWS service**. Use case: **Lambda**.
5. Attach only **AWSLambdaBasicExecutionRole**.
6. Role name: `sample-create-order-role`.
7. Create the role.

### Paste the policy

1. Open [bucket-policy.json](bucket-policy.json).
2. Replace both copies of `ACCOUNTID` with the 12-digit account id. One is in the role ARN. One is in the bucket name. Do not leave the word `ACCOUNTID` in the JSON.
3. In the bucket, open **Permissions**, then **Bucket policy**, then **Edit**.
4. Paste the JSON and save.

Expected statement:

- Effect **Allow**
- Principal `arn:aws:iam::ACCOUNTID:role/sample-create-order-role`
- Actions `s3:GetObject` and `s3:PutObject`
- Resource `arn:aws:s3:::sample-orders-invoices-ACCOUNTID/*`

Leave **Block Public Access** on. Do not add a statement with `Principal: *`. Do not add an explicit **Deny**. A deny for everyone except one role is easy to mistype, and a mistake can lock you out of the bucket, including deleting it.

This Allow does not, by itself, stop another IAM user in the same account who already has `s3:PutObject` from uploading. It documents the application role. It is not a lock on the rest of the account.

If save fails, the role ARN does not exist or the JSON has a trailing comma. Fix the ARN. Do not turn off Block Public Access to force the save.

## 7. Write two sentences

On paper, answer both:

1. Someone uploaded the wrong body for `invoice.txt`, and versioning is on. What is the recovery point (how much of the invoice did you lose), and what do you download to get the previous body back?
2. What would a cross-region replication rule add that versioning in Mumbai does not? The diagram target is a bucket in `ap-southeast-1` (Singapore). You are not creating that bucket.

A good pair of answers: the previous version is still in this bucket, so a bad overwrite loses nothing if you restore that version, and the restore is a short task. Replication would put new versions in another region after a lag. Versioning in Mumbai does not help if Mumbai itself is unavailable. Do not open the replication wizard.

## 8. Delete what you created

1. Open the bucket. Choose **Empty**.
2. The empty action must delete **all versions and delete markers**, not only the current object. Type the confirmation the console asks for.
3. After the bucket is empty, **Delete** the bucket.
4. If this demo created `sample-create-order-role` and nothing else uses it, delete that role in IAM. If the role already existed for another lab, leave it.
5. Set the region selector back through the list and confirm you did not create a bucket in **Asia Pacific (Singapore) ap-southeast-1**.

## Done when

- You downloaded `version one` after `version two` was the current object.
- Versioning is on, encryption is SSE-S3, and Block Public Access is still on.
- The bucket policy names `sample-create-order-role`.
- The bucket and its versions are gone.
