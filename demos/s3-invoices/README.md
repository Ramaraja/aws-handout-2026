# Sample Orders invoice bucket

A console demo of the Module 8 bucket. You create one versioned, encrypted invoice bucket in `ap-south-1`, overwrite one object, restore the older version, add a lifecycle rule, and attach a bucket policy.

Follow [SETUP.md](SETUP.md). Do not create a replication rule and do not open a bucket in Singapore.

## Names

| Piece | Name |
| --- | --- |
| Region | `ap-south-1` |
| Bucket | `sample-orders-invoices-` plus the 12-digit account id |
| Object key | `invoice.txt` |
| Lifecycle rule | `expire-noncurrent-invoices` |
| Role | `sample-create-order-role` |

## What you will see

- Block Public Access stays on.
- Default encryption is SSE-S3.
- Two versions of `invoice.txt`. The current body is `version two`. The older body is still `version one`.
- The bucket policy allows the role `s3:GetObject` and `s3:PutObject`. It does not deny every other user in the account.

## Files

| File | Use |
| --- | --- |
| [SETUP.md](SETUP.md) | Console steps. |
| [bucket-policy.json](bucket-policy.json) | Paste this after you replace `ACCOUNTID`. |
