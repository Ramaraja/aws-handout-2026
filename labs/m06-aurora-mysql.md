# Module 6 lab: Tour sample-orders-db

**Time:** 35 minutes  
**Region:** ap-south-1  
**You will create:** nothing  
**You will not do:** failover, modify capacity, turn on public access, or delete the cluster yourself

The instructor deletes the cluster at the end of the session.

## 1. Find the writer

1. Set the region to **ap-south-1**.
2. Open **RDS** → **Databases** → `sample-orders-db`.
3. Record the engine and the status.
4. Copy the **writer endpoint**.
5. Record whether a reader instance exists.

## 2. Check the network

1. Open the subnet group. Write down two Availability Zones it uses.
2. Open the security group. Write the inbound rule for port **3306**, including the source.
3. Record the public-access setting.
4. Write one sentence: why your laptop is not the right client for this endpoint.

## 3. Check backup

1. Find the backup retention period.
2. Find the earliest restorable time, if it is already shown.
3. Write one sentence: a point-in-time restore creates a new cluster. It does not rewind this one in place.

## 4. Read two metrics

1. Open **Monitoring**.
2. Record the latest `CPUUtilization` and `DatabaseConnections`.
3. If the query editor is available and the instructor opens it, watch `SELECT 1` or `SHOW DATABASES`. If it is not available, write “query editor not used” and stay on the metrics.

## 5. Stop

Do not click Delete, Failover, or Modify. Tell the instructor when your notes are complete so they can delete the cluster, skip the final snapshot, and drop retained automated backups.

## Done when

- You have the writer endpoint, the public-access value, the port 3306 source, and two metric readings.
- You did not leave a second cluster or a snapshot of your own.
