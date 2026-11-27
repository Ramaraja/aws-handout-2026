# Module 10 lab: Tabletop for a lost region

**Time:** 35 minutes  
**You will create:** nothing in AWS

Work in pairs. Use the names from class. The second region is `ap-southeast-1` on paper only. Do not open a replication or database wizard.

## The incident

Mumbai (`ap-south-1`) is unavailable. Sample’s targets are:

- **RTO:** 4 hours
- **RPO:** 15 minutes

Multi-AZ inside Mumbai is not available, because the region is the failure.

## Fill this table

For each component, pick one pattern: backup/restore, pilot light, warm standby, or active-active. Add one sentence on what must already exist before the failure.

| Component | Pattern | What must already exist |
| --- | --- | --- |
| `sample-create-order` |  |  |
| Invoice bucket |  |  |
| `sample-orders-db` |  |  |
| `sample-nightly-orders` and its script |  |  |

## Answer these

1. Why is S3 versioning in Mumbai not enough for this incident?
2. Why is Aurora failover to another zone not enough for this incident?
3. A cross-region replica has been copying deletes all day, and someone dropped the `orders` table an hour ago. Does the replica save you? What does?

## Done when

- All four rows are filled.
- The three questions have answers.
- The account has no new bucket, replica, or cluster.
