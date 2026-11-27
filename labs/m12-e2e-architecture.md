# Module 12 lab: Repair the flawed Sample Orders design

**Time:** 35 minutes  
**You will create:** nothing

Work in pairs. The good system is the one from the course. The list below is a bad build of that same system. For each flaw, name the repair and the module idea you are using. Do not add a new AWS product.

## Flaws

1. `sample-orders-db` is publicly accessible. `sample-aurora-sg` allows TCP 3306 from `0.0.0.0/0`.
2. The invoice bucket has Block Public Access turned off, and the bucket policy allows `s3:GetObject` for `Principal: *`.
3. `inventory-queue` has no dead-letter queue. `sample-inventory-worker` throws on bad JSON, and the message is received again every time the visibility timeout ends.
4. There is no alarm on `sample-create-order` and no alarm on queue age.
5. The account has no CloudTrail trail, and nobody reviewed event history after the bucket policy changed.
6. A design note says one Availability Zone is enough for the database, and that S3 versioning is the plan if `ap-south-1` is lost. The stated targets, if the region is lost, are an RTO of 4 hours and an RPO of 15 minutes.

## Write this

| Flaw | Repair | Why this is enough |
| --- | --- | --- |
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |
| 4 |  |  |
| 5 |  |  |
| 6 |  |  |

## Also answer

- Which resource would the stack `sample-invoice-bucket` own?
- Why is a NAT gateway not the fix for flaw 1?

## Done when

- All six rows are filled.
- You created no resources.
- You can explain flaw 6 without calling Multi-AZ a second region.
