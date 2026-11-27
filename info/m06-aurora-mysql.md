# Aurora MySQL

**Handout.** Region: **ap-south-1** (Mumbai).

You read the database that stores the order row. If cluster `sample-orders-db` is already available, use it. Do not launch a cluster just to look. If you create one, delete it the same day.

## Goals

By the end of this handout you can explain:

1. An Aurora MySQL cluster as a shared storage volume plus a writer and optional readers.
2. Where to find the writer endpoint, the subnet group, and the security group, and why the cluster is not public.
3. How automated backups, point-in-time restore, and snapshots differ, and what a failover changes.
4. How to use the monitoring tab to separate “the database is busy” from “the application cannot connect.”

## Architecture and components

Aurora MySQL is a managed database that speaks the MySQL protocol. Sample’s application uses a normal MySQL driver. The architecture under that protocol is not a single EBS volume on one instance.

| Piece | Sample Orders name | What it is |
| --- | --- | --- |
| Cluster | `sample-orders-db` | The unit you back up and fail over. |
| Storage volume | cluster storage | Replicated across three Availability Zones by Aurora. You do not pick a volume size for a small cluster. |
| Writer instance | the writer in the cluster | Takes reads and writes. There is one writer. |
| Reader instance | none required | Takes reads. A reader in another zone is the usual failover target. Serverless v2 can add readers. A practice cluster may be writer-only. |
| Writer endpoint | hostname on the cluster | The name applications use for writes. It follows the writer. After failover it points at the new writer. |
| Reader endpoint | the cluster reader endpoint | Load-balances readers. If there is no reader, do not send the packing service here and expect reads to succeed. |
| Database | `orders` | A schema inside the cluster, created at launch. |

Amazon RDS for MySQL is an instance with its own storage, and a Multi-AZ standby is a second copy. Aurora separates compute (the instance) from a shared storage volume that is already spread across zones. Failover promotes another instance to writer. It does not restore a snapshot. That is why a short Multi-AZ recovery time still needs snapshots for a region failure. Snapshots and Multi-AZ solve different problems.

Serverless v2 scales capacity in ACUs. A practice cluster uses minimum **0.5** and maximum **1** so it cannot scale an expensive peak. 0.5 ACU is still a running database. It bills while it exists. “Serverless” here does not mean the bill is zero between SQL statements.

The application table:

```sql
CREATE TABLE orders (
  order_id VARCHAR(36) PRIMARY KEY,
  sku VARCHAR(64) NOT NULL,
  qty INT NOT NULL,
  status VARCHAR(32) NOT NULL
);
```

You can read that statement without running it. It makes “the row lives here” concrete. Run it only if you will drop it before you delete the cluster.

## Connectivity, security, and configuration

The cluster is in a subnet group with subnets in at least two Availability Zones. Aurora needs that even when you have one writer. The data is not “in one subnet.” The instance’s network interface is in one subnet at a time.

**Public access is No.** There is no public IP. A laptop on the public internet cannot open port 3306 to this cluster, and it should not. `sample-aurora-sg` should allow TCP 3306 only from application security groups such as `sample-lambda-sg` or `sample-fargate-sg`. A default security group on a practice cluster is a shortcut. Read the rule. If the rule is `0.0.0.0/0`, that is a flaw to tighten, not a setup to copy.

How an application connects:

- Host: the **writer endpoint**, not the instance’s IP. The IP changes. The endpoint is updated on failover.
- Port: **3306**.
- Database name: `orders`.
- Credentials: the master user `sample_admin` and a password in Secrets Manager, or IAM database authentication later. The password is not in the task definition, a document, or a chat. The query editor uses the stored secret.

A Lambda function reaches this endpoint only if it is in the VPC, its subnets can route to the database subnets, and the security group allows it. The first order function was not in a VPC. Putting it in a VPC to reach Aurora brings back the NAT-or-endpoint choice. Do not attach the function as part of this tour.

The query editor, when the console offers it, runs SQL from the AWS network using the stored secret. If the button is absent, skip SQL. Absence of the button is not an outage. Do not build a bastion host.

## Backup, recovery, and high availability

Three mechanisms, and they are not interchangeable:

- **Automated backups** and **point-in-time restore** use the continuous backup and transaction log. Retention on a practice cluster is **1 day**. You can restore to a time inside that window. Restore creates a **new** cluster. It does not rewind the existing one in place.
- A **snapshot** is a copy you take on purpose or that AWS takes as part of the backup window. You can copy a snapshot to another region. That is the bridge to disaster recovery. Snapshot storage is billed after the cluster is deleted if you keep it.
- **Failover** moves the writer role to another instance in the same region, or Aurora replaces the writer. The writer endpoint stays the name applications already use. In-flight transactions fail and the application retries. Failover is for an instance or zone problem. It does not help if the region is unavailable, and it does not help if someone drops the `orders` table. A dropped table needs PITR or a snapshot.

Turn deletion protection **on** for a database you mean to keep. Turn it **off** only on a practice cluster you will delete the same day.

You do not need to click **Failover** to understand it. On a writer-only Serverless cluster it can take several minutes. What you would see: connections drop, the writer endpoint starts resolving to the new instance, and CloudWatch shows a failover event.

## Monitoring and troubleshooting

Stay on the cluster’s **Monitoring** tab and CloudWatch.

| Metric | A basic reading |
| --- | --- |
| `CPUUtilization` | The writer is busy. It does not, by itself, mean the security group is wrong. |
| `DatabaseConnections` | Applications are holding sessions. A sudden drop during an error burst suggests they cannot connect or are crashing. |
| `FreeableMemory` | Memory pressure on the instance. |
| Replica lag | Only if a reader exists. A reader far behind is a stale read, not a failed write. |

A single slow `SELECT` is an index or a query problem. It is not fixed by adding a region. Performance Insights is optional. Naming it is enough.

A connection failure path for Sample Orders:

1. Application timeout or “cannot connect” in the Lambda or Fargate log.
2. Security group: no inbound 3306 from the caller’s group.
3. Network: caller is outside the VPC, or in a subnet that cannot route to the instance.
4. DNS: the application cached the old IP instead of the writer endpoint. It should use the endpoint name.
5. Auth: wrong secret, or the user has no grant on `orders`.

Public access and a wide-open security group would make step 2 succeed from the internet. That is not the fix.

## In the console

### 1. Read the cluster shape

1. Region **ap-south-1**. **RDS** → **Databases**.
2. Open `sample-orders-db` if it is **Available**. If it is not there, read the settings below and do not launch a cluster just to look.
3. Note the writer instance and, if present, a reader.
4. Copy the **writer endpoint**. Note whether a reader exists before you use the reader endpoint.
5. Open the subnet group and name two Availability Zones.
6. Open the VPC security group. Read the inbound rule. Compare it with “3306 from the application only.”

**Expected:** public access is No. Capacity is Serverless v2, max 1 ACU.

**If the cluster is still creating:** read the same fields from the configuration summary. Do not launch a second cluster.

### 2. Read backup settings

1. On the cluster, open maintenance and backups.
2. Note retention of 1 day and the earliest restorable time.
3. Restore creates a new cluster. Do not start a restore while you are only reading.

### 3. Monitoring

1. Open **Monitoring**.
2. Find `CPUUtilization` and `DatabaseConnections`.
3. With no application connected, connections near zero are healthy, not an outage.

### 4. Optional query

If **Query Editor** is available for this cluster:

1. Connect with the stored secret and database `orders`.
2. Run `SHOW DATABASES;` or `SELECT 1;`.
3. Skip `CREATE TABLE` unless you will drop it before delete.

If Query Editor is not available, stay on the monitoring tab.

## When you are done

If you created the cluster for this exercise, delete it the same day. If you are only reading a shared cluster, do not click Modify, Failover, or Delete.

1. Select the cluster `sample-orders-db`.
2. Delete. Skip the final snapshot. Do not keep automated backups.
3. If the console asks you to delete instances first, delete the instances, then the cluster.
4. Confirm the database list no longer shows `sample-orders-db` or a leftover snapshot.

**If deletion is blocked:** deletion protection is on. Turn it off, then delete. A snapshot left behind will bill. Delete that snapshot unless you have a reason to keep it for a restore drill the same day.

The useful notes from a tour are the endpoint name, the public-access value, the security group rule, and one metric reading.

## What this costs

This is the expensive resource in the set. The cluster must not survive the day if you created it to practice. Snapshot and automated-backup retention after delete are easy to miss. Check **Snapshots** before you leave.
