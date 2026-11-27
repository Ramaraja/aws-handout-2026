# Disaster recovery

**Handout.** Region: **ap-south-1** (Mumbai).

You choose how Sample Orders recovers. The discussion uses Mumbai and, on paper only, Singapore. You create nothing.

## Goals

By the end of this handout you can explain:

1. RTO and RPO, and where backup and restore, pilot light, warm standby, and active-active sit on those axes.
2. A recovery approach for Lambda, Glue, S3, and Aurora that matches a stated RTO and RPO.
3. What Multi-AZ protects, and what only a second region protects.
4. A tabletop for Sample Orders that does not create a second environment.

## Patterns

- **RPO** is how much data you can lose, measured in time. An RPO of 15 minutes means you must have a copy of data that is never more than 15 minutes behind.
- **RTO** is how long you can be down. An RTO of 4 hours means the service must be taking orders again within 4 hours.

A pattern is a way of spending money before the failure so those two numbers are achievable.

| Pattern | What is already running in the second place | Typical cost | Typical RTO |
| --- | --- | --- | --- |
| Backup and restore | Nothing. You have backups and templates. | Lowest | Hours, sometimes longer |
| Pilot light | The hard-to-create core, small. For Sample Orders, a database replica or a copied snapshot path, not the full API at full size. | Low | Tens of minutes to hours |
| Warm standby | A scaled-down copy of the stack that you can grow. | Medium | Minutes to tens of minutes |
| Active-active | Both regions take traffic. | Highest | Seconds to minutes, if clients can fail over |

You pay more, continuously, to make RTO shorter. RPO is mostly about how you replicate data, not about how many Lambda functions are warm.

The Sample Orders tabletop is not active-active. Active-active is the answer when the business says both RTO and RPO are near zero and it will run two live stacks: two of every regional resource, conflict handling on writes, and a way to shift traffic.

## Lambda

`sample-create-order` and the workers are stateless. The code is the asset. A region loss means: deploy the same function and the same API in `ap-southeast-1`, point the role at the resources in that region, and send traffic there.

Versions and aliases matter. An alias `live` points at a version. Rollback is moving the alias, the same idea as a previous task-definition revision for Fargate. For disaster recovery, the alias is what you promote in the new region after you publish the same version.

Lambda does not store the order. Recovering the function without recovering Aurora and S3 restores an API that accepts writes into an empty database. The function is the easy part.

Multi-AZ is not a setting you toggle on a function. AWS already runs the Lambda service across zones in the region. A zone failure is AWS’s problem unless the function is pinned to one subnet in a VPC and that subnet is the one that failed. The first order function was not in a VPC. A **region** failure is yours to recover.

## Glue

`sample-nightly-orders` is a job definition plus a script object in S3. Recovering it is a redeploy, like Lambda, if the script and the job definition are not only in the failed region. The script bucket needs the same thinking as the invoice bucket: versioning, and a cross-region copy if the script must exist after Mumbai is unavailable.

The Data Catalog in `ap-south-1` is not the catalog in `ap-southeast-1`. A crawler must run again, or you recreate the table. The CSV it reads should be in the region where the job runs. Cross-region reads are a poor default. Replicate the export, then run the job beside the replica.

Glue does not give you Multi-AZ as a product switch. A failed job run is a retry in Step Functions, not a regional failover.

## S3

- A bad overwrite or a delete marker: versioning, short RTO, RPO near zero for that mistake. This is not a regional failover.
- A lost region: CRR to `ap-southeast-1`, RPO equals replication lag, RTO equals the time to point readers at the replica bucket. Objects that had not finished replicating are the loss.
- Lifecycle expiration is not a recovery tool. It deletes.

Multi-AZ for standard S3 storage is AWS’s durability and availability design inside the region. You do not place an object in one zone yourself. You also do not get a second region from that design. CRR is the multi-region control. You can select it in a design without creating the rule.

## Aurora and RDS

- The storage is already replicated across three zones. A writer failover is **Multi-AZ**. RTO is short: reconnect to the same writer endpoint. RPO for a failover is typically near zero because the storage volume is shared. In-flight transactions that did not commit are the loss, and the application retries.
- Multi-AZ does nothing for a lost region, a bad deploy that deletes rows, or an account-level mistake. Those need backups.
- Automated backups and point-in-time restore: RPO can be very small because Aurora’s backup is continuous within retention. RTO is the time to restore a **new** cluster and repoint applications. That is backup and restore, and it can miss a 30-minute RTO if restore takes longer.
- A cross-region snapshot copy is backup and restore with a longer RPO if copies are infrequent.
- An Aurora **global database** or a cross-region read replica puts a replica in `ap-southeast-1`. That is pilot light or warm standby for the database. RPO is the replication lag, often seconds. RTO is the time to promote the secondary and repoint the application. A cross-region replica is a real monthly cost. Write the choice down before you create one. Choose it when the RPO is 15 minutes and a snapshot that is hours old is too old.

RDS MySQL Multi-AZ is a standby in another zone. A standby in another zone is still one region. Sample’s database is Aurora.

## Multi-AZ next to a second region

| Failure | Multi-AZ | Second region |
| --- | --- | --- |
| One zone in Mumbai | Aurora failover. Lambda keeps running. S3 stays available. | Not required |
| Bad invoice upload | S3 versioning | Not required |
| Mumbai unavailable | Not enough | Redeploy Lambda and Glue. Read S3 from the replica. Promote or restore Aurora. |
| Dropped table | Restore or PITR in-region | A replica may have replicated the drop. Backups still matter. |

A replica is not a backup. If the application deletes every row and replication is fast, the second region deletes every row too. Backups and a lag you can recover from protect you from your own writes.

## Tabletop

No resource to create. Use this incident: `ap-south-1` is unavailable, RTO is 4 hours, RPO is 15 minutes.

| Component | Pattern | Why |
| --- | --- | --- |
| `sample-create-order` | Backup and restore by redeploy, or pilot light if the API is already scripted | No data. An RTO of 4 hours is enough to deploy a function. The code and template must already exist. |
| Invoice bucket | CRR, which is pilot light for the objects | An RPO of 15 minutes requires replication lag inside 15 minutes, not a nightly copy. Versioning alone does not survive a lost region. |
| `sample-orders-db` | Pilot light: cross-region replica or global database, plus backups | A nightly snapshot can miss a 15-minute RPO. Multi-AZ does not survive the loss of Mumbai. |
| `sample-nightly-orders` | Redeploy the job and replicate the script and the CSV | The job is code. The CSV is data and follows the S3 rule. |

Active-active for all four needs an answer to who takes writes in both regions and what happens when both update `ord-1001`. An RTO of 4 hours does not require that design.

Multi-AZ for the database under a regional outage is the wrong scope. Multi-AZ answers a zone failure inside Mumbai.

## When you are done

Nothing to delete if you only wrote the table. If you opened the console and created anything, delete it. Do not open the replication wizard for this exercise.

## What this costs

This exercise spends nothing if you create nothing. The designs, especially a cross-region Aurora replica, are real monthly costs. The point of the tabletop is to choose them before you click them.
