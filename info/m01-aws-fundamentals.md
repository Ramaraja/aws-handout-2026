# AWS and cloud fundamentals

**Handout.** Region: **ap-south-1** (Mumbai).

Sample Orders is a small retailer. You follow one order from the account and the region through the services that hold the API, the function, the database, and the invoice. You create only the monthly budget `sample-orders-training`.

## Goals

By the end of this handout you can explain:

1. What cloud computing changes for an application team, and where the shared-responsibility line sits for a managed service.
2. How a workload sits in a Region and an Availability Zone, and how a global service differs from a regional one.
3. Which core service fills each box in Sample Orders.
4. How to protect the account root, require MFA, and notice spend with a monthly budget alarm.

## Cloud computing and AWS fundamentals

Cloud computing is renting capacity and managed services instead of buying servers for a peak that may never come. For Sample Orders, the team describes an API, a function, a database, and a bucket. AWS runs the hardware, the hypervisor, and the building.

Three service styles are enough to place the later topics:

- **Infrastructure you configure.** Amazon EC2 is a virtual machine. You choose the image, the size, and the network. Sample Orders does not run the API on EC2. The packing service uses a container service instead.
- **Platform you deploy onto.** AWS Lambda runs a function. Amazon ECS on Fargate runs a container. You still own the code and the configuration.
- **Software you call.** Amazon SQS, Amazon SNS, and Amazon S3 are APIs. You do not patch those servers.

Shared responsibility is the line that is easy to draw in the wrong place. AWS operates the cloud: facilities, hardware, and the managed service control plane. The account owner operates in the cloud: account access, data, network rules, and application code. For Aurora, AWS patches the database engine fleet and replicates storage. Sample Orders still chooses who can connect, what the security group allows, and whether deletion protection is on. For S3, AWS provides the durability of the storage system. Sample Orders still decides whether a bucket is public and whether objects are encrypted.

A managed service is not a security boundary you can ignore. The API call still runs as an identity you created.

Pricing models to name, without a price sheet:

- Pay for what you provision (an EC2 instance hour, a NAT gateway hour).
- Pay for what you use (Lambda requests and duration, S3 storage and requests, SQS requests).
- A free tier that expires or that only covers the first units. Hourly resources still bill. The budget you create is the control.

## Regions, Availability Zones, and global infrastructure

A **Region** is a cluster of data centers in a geography. `ap-south-1` is Mumbai. Almost every resource Sample Orders creates is regional. A Lambda function in Mumbai does not exist in Singapore. A bucket lives in one region unless you add replication. You do not create that rule in this handout.

An **Availability Zone** is one or more data centers in that region with independent power and networking. `ap-south-1a` and `ap-south-1b` are two zones you can use in a design. The letters are an account-level alias. Your `ap-south-1a` is not guaranteed to be the same building as another account’s `ap-south-1a`. Design for two zones, not for a specific building.

Why Sample Orders cares:

- The VPC has a public and a private subnet in each of two zones.
- Aurora requires a subnet group that spans at least two zones, even for a small cluster.
- A single zone failure should not be the availability plan. Multi-AZ versus a second region is covered with disaster recovery. A zone is smaller than a region.

**Global** services are the exception. IAM is global. An IAM role is not created “in Mumbai.” Amazon CloudFront and Route 53 are global edge and DNS services. Sample Orders does not build either one. A role lives in the account, in every region.

Edge locations cache content close to users. Sample Orders does not put the API on CloudFront.

Look at the region selector before you click Create. A resource created in `us-east-1` is invisible while the console is showing `ap-south-1`.

## Console and core services

The console is a web front end on the same APIs the CLI and CloudFormation call. Searching for the service name is more reliable than memorizing the left nav.

| Service | What to remember | Sample Orders piece |
| --- | --- | --- |
| IAM | Identities and permissions | `sample-create-order-role` |
| VPC | Your private network in one region | `sample-orders-vpc` |
| Lambda | A function, run on demand | `sample-create-order` |
| API Gateway | An HTTP front door to the function | `sample-orders-api` |
| SQS and SNS | Queue and fan-out topic | `inventory-queue`, `order-events` |
| ECS | Run a container without managing servers, on Fargate | `sample-packing` |
| Aurora | MySQL-compatible database cluster | `sample-orders-db` |
| CloudWatch | Metrics, logs, alarms | dashboard `sample-orders` |
| S3 | Objects in a bucket | `sample-orders-invoices-ACCOUNTID` |
| Glue and Step Functions | A data job and a workflow | `sample-nightly-orders`, `sample-nightly-etl` |
| CloudFormation | A template that creates a stack | `sample-invoice-bucket` |
| CloudTrail | A record of API calls | `sample-management-trail` |

EC2 is on the map because it is the familiar “server.” Sample’s request path does not include an EC2 instance. Fargate still runs on EC2 capacity that AWS manages. You do not pick the instance.

## Basic architecture and application components

Four layers hold Sample Orders:

- **Edge / entry.** The client and API Gateway. Something on the public internet calls `POST /orders`.
- **Compute.** Lambda for the write path and the queue workers. Fargate for the packing service, which is a longer-running process than a single HTTP request.
- **Integration.** SNS and SQS sit between the API and the workers so the HTTP call does not wait for email and inventory.
- **Data.** Aurora holds the order row. S3 holds the invoice object. They fail and recover differently.

Two boundaries show up again later:

- **Network.** Lambda and Aurora sit in the VPC. The client does not.
- **Identity.** Each compute piece assumes a role. The role is what allows the function to publish to SNS or write to Aurora. A user password inside the function is the wrong tool.

Limits that change the shape of Sample Orders:

- A Lambda function’s maximum timeout is 15 minutes. A nightly export that might run longer belongs in a job (Glue) or a container, orchestrated by Step Functions. That is why Sample Orders has both a function and a Glue job.
- An API Gateway payload is not a place to upload an invoice PDF. The invoice goes to S3. The API returns an id.
- SQS messages are limited to 256 KB. An order event is a small JSON document, not the invoice file.

## Account, security, and cost

The **root user** is the email address that created the account. It can close the account. It is not a daily login. Turn on MFA for root. Use an IAM user or a role for ordinary work.

An **IAM user** is a person or an application that signs in with long-lived credentials. Prefer a role when the organization already has SSO. You do not need access keys for this handout.

A **budget** does not stop spending by itself. A cost budget with an email alert tells you when the month crosses 80 percent and 100 percent of 20 USD. Stay inside that amount by skipping a NAT gateway, an interface VPC endpoint, a second-region database, and cross-region replication. A NAT gateway or a forgotten Aurora cluster will blow past 20 USD. The budget is how you notice. Deleting what you create is how you prevent it.

Pricing habits:

- Regional services bill in the region where the resource runs.
- Data transfer between zones and out to the internet costs money. Practice volume is tiny. Hourly charges are not.
- Delete what you create. Versioned buckets and database snapshots can bill after the resource looks gone.

## In the console

### 1. Confirm the region

1. Sign in to the console.
2. In the top bar, open the region selector. Choose **Asia Pacific (Mumbai) ap-south-1**.

**Expected:** the selector reads Asia Pacific (Mumbai).

**If the account cannot use that region:** stay in the one region the account allows for every later example. Do not mix regions.

### 2. Read the account id

1. Search for **IAM** and open it.
2. Open the dashboard. Note the 12-digit account id. The invoice bucket name uses those digits.
3. Confirm MFA on root is enabled. If it is not, stop and ask the account owner to turn it on. Do not sign in as root, and do not share root credentials.

### 3. Create the budget

Skip creation if `sample-orders-training` already exists. Open it and read the two thresholds instead.

1. Search for **Budgets** and open **Billing and Cost Management**.
2. Choose **Create budget**.
3. Choose a **cost budget** (customize, not a reservation or savings-plan budget).
4. Period **Monthly**. Budget amount **20** USD. Name `sample-orders-training`.
5. Add an alert at **80** percent of budgeted amount, and a second at **100** percent. Send both to your email.
6. Create the budget.

**Expected:** the budget appears in the list with a current spend near zero and two alert recipients.

**If you cannot open Billing:** skip this step. Do not sign in as root to grant yourself access.

### 4. Place Sample Orders on the diagram

On paper, write the four layers (entry, compute, integration, data) and place these names:

- `sample-orders-api`
- `sample-create-order`
- `order-events`, `inventory-queue`, `notify-queue`
- `sample-orders-db`
- `sample-orders-invoices-ACCOUNTID`

## When you are done

Leave the budget in place. It is the cost guard for the later examples. Create nothing else.

## What this costs

The budget itself should be free as one of the first two budgets in the account. This section creates no hourly resources. If the alert fires, check for a NAT gateway, an Aurora cluster, a Fargate service, or a load balancer left running.
