# Networking and security

**Handout.** Region: **ap-south-1** (Mumbai).

You build the network Sample Orders uses and the role the order function assumes. You create `sample-orders-vpc` and `sample-create-order-role`. You do not create a NAT gateway, a VPC endpoint, or an EC2 instance.

## Goals

By the end of this handout you can explain:

1. How to size a VPC and split it into public and private subnets across two Availability Zones.
2. How a route reaches an internet gateway, why a short exercise skips the NAT gateway, and when a security group is the right place for an application rule.
3. How an IAM user differs from a role, and a trust policy from a permissions policy.
4. How a gateway VPC endpoint differs from an interface endpoint, including why only one of them is free to add.

## VPC, CIDR, and subnets

A VPC is your network in one region. Sample’s is `sample-orders-vpc` in `ap-south-1`, CIDR `10.0.0.0/16`. The `/16` means the first 16 bits are the network. That leaves 16 bits of host space, 65,536 addresses, of which AWS reserves a few in every subnet. A practice VPC will not run out of addresses. A real account can, if every subnet is a `/24` and the VPC was carved too small. `/16` is a sound starting size.

A subnet is a slice of that CIDR in **one** Availability Zone. Sample Orders uses four:

| Subnet | CIDR | Zone | Role |
| --- | --- | --- | --- |
| Public A | `10.0.1.0/24` | `ap-south-1a` | Has a route to the internet gateway |
| Public B | `10.0.2.0/24` | `ap-south-1b` | Same, second zone |
| Private A | `10.0.11.0/24` | `ap-south-1a` | No route to the internet gateway |
| Private B | `10.0.12.0/24` | `ap-south-1b` | No route to the internet gateway |

A `/24` is 256 addresses. AWS reserves five in each subnet (network, router, DNS, future use, and broadcast). “Public” does not mean the subnet is open to the world. It means the route table points `0.0.0.0/0` at an internet gateway, and the resource has a public IP. “Private” means there is no such route. Aurora belongs in the private subnets. A load balancer, if you had one, would sit in the public subnets. Sample Orders does not create a load balancer here.

CIDR blocks must not overlap inside the VPC. `10.0.1.0/24` and `10.0.2.0/24` do not overlap. `10.0.1.0/24` and `10.0.1.0/25` would. If two VPCs are later peered, their CIDRs also must not overlap.

The console can create “VPC and more.” That wizard will add a NAT gateway unless you set it to **None**. A NAT gateway is billed per hour plus data.

## Routing, internet gateway, NAT, and security groups

A route table is a list of “where next.” The main rules for Sample Orders:

- Local route `10.0.0.0/16` → local. Traffic inside the VPC does not leave AWS’s network.
- Public route table: `0.0.0.0/0` → `sample-orders-igw`.
- Private route table: no `0.0.0.0/0` route in this example.

An **internet gateway** is a horizontally scaled VPC component that allows traffic between the VPC and the internet. It is not a virtual machine you patch. It has no hourly charge. Attaching one does not expose your instances. A security group still has to allow the flow, and the instance needs a public IP for inbound connections from the internet.

A **NAT gateway** lets private subnets open outbound connections (pull an OS update, call a public API) without accepting inbound connections from the internet. It is the right production tool for a private subnet that must reach out. It is the wrong tool for a short exercise. One NAT gateway in one zone is a single path out, and it bills even when idle. Draw `0.0.0.0/0` → NAT on the private route table when you need that path. Do not create the gateway for this example.

**Security groups** are the application firewall here.

- Attached to a network interface (the Lambda ENI, the Aurora ENI, the Fargate task ENI), not to a subnet.
- Allow rules only. There is no deny rule.
- Stateful. If you allow inbound port 3306 from the Lambda security group, the return traffic is allowed without a second rule.
- You can reference another security group as the source. That is what Sample Orders wants: `sample-aurora-sg` allows TCP 3306 from `sample-lambda-sg`, not from `0.0.0.0/0`.

**Network ACLs** sit on the subnet, are stateless, and can deny. They are optional defense in depth. They are a poor place for an application rule because you must allow both directions and the ephemeral return ports. Default NACLs allow all. Leave them there unless you have a subnet-wide deny to add.

For Sample Orders:

- `sample-lambda-sg`: outbound HTTPS 443 to anywhere is enough for a function that calls AWS APIs through the internet. In a private subnet without NAT, that outbound path does not exist. The first Lambda example stays out of the VPC, so it reaches AWS APIs on the AWS network without this VPC.
- `sample-aurora-sg`: inbound 3306 from `sample-lambda-sg` only. No public IP on the database.

Lambda in a VPC is an extra choice. It gives the function a private path to Aurora. It also means the function needs a way out to other AWS APIs, which is either NAT or a VPC endpoint. The first function stays out of the VPC on purpose.

## IAM users, roles, and policies

- An **IAM user** is a long-lived identity with a password or access keys. A person may be a user. The function is not a user.
- An **IAM role** is an identity that is assumed. `sample-create-order` assumes `sample-create-order-role` for the duration of an invocation. There is no password inside the zip file.
- A **policy** is a document of permissions. It is not an identity.

Two policies hang off a role:

- The **trust policy** (assume-role policy) answers “who can become this role?” For this role the principal is `lambda.amazonaws.com`. API Gateway does not assume the function’s role. Lambda does, when it runs the function.
- The **permissions policy** answers “what can this role do?” `AWSLambdaBasicExecutionRole` lets the function write logs to CloudWatch. Later sections add `sqs:SendMessage`, `sns:Publish`, or `s3:PutObject` on specific resource ARNs. Start small.

A user policy and a role policy are the same kind of document. The difference is which identity you attach it to. A bucket policy is a third place a policy can live: on the bucket, not on the role. The bucket can also say who is allowed, and an explicit deny there wins.

The create-order role does not get `AdministratorAccess`. If the Lambda wizard offers to create a role with basic execution, that is the right width. If it offers a role that can access all S3 buckets, reject it.

Identity policies are evaluated with resource policies, SCPs, and permission boundaries. An explicit deny wins. This account should not hand out admin keys for a practice function.

## Gateway and interface VPC endpoints

Without an endpoint, a function in a private subnet reaches S3 by going out to the public S3 endpoint. That requires NAT if the subnet is private. A VPC endpoint keeps that traffic on the AWS network.

**Gateway endpoints** exist for S3 and DynamoDB.

- You add a route in the route table to a prefix list.
- There is no elastic network interface and no hourly charge.
- They are the right default when a private subnet must reach S3.

**Interface endpoints** (PrivateLink) exist for most other APIs, including CloudWatch Logs, Secrets Manager, and API Gateway execute-api.

- AWS places an ENI in your subnet with a private IP.
- You pay per hour per Availability Zone, plus data.
- Two zones means two hourly charges. This example creates none.

Know both. Create neither for this walkthrough.

## In the console

### 1. Create the VPC with NAT set to None

1. Set the region to **ap-south-1**.
2. Search for **VPC**. Choose **Create VPC**.
3. Choose **VPC and more**.
4. Name tag auto-generation: `sample-orders`. The VPC itself should be named `sample-orders-vpc`. If the wizard only offers a name prefix, use `sample-orders` and then rename the VPC resource to `sample-orders-vpc` after creation.
5. IPv4 CIDR `10.0.0.0/16`.
6. Availability Zones: **2**.
7. Public subnets: **2**. Private subnets: **2**.
8. NAT gateways: **None**.
9. VPC endpoints: **None**.
10. DNS hostnames: enabled.
11. Create the VPC. Wait until the subnets are available.

**Expected:** one VPC, four subnets, one internet gateway attached, a public route table with `0.0.0.0/0` to the IGW, a private route table with only the local route.

**If it fails:** a quota or a CIDR overlap with an existing VPC. Pick `10.20.0.0/16` only if `10.0.0.0/16` is taken, and use that CIDR in every later note for this account.

Open the public route table and find the IGW route. Open the private route table and confirm there is no default route. That absence is the point of the example.

### 2. Create the Lambda role

1. Search for **IAM** → **Roles** → **Create role**.
2. Trusted entity type: **AWS service**. Use case: **Lambda**.
3. Attach the managed policy **AWSLambdaBasicExecutionRole**. Do not attach `AdministratorAccess`.
4. Name the role `sample-create-order-role`.
5. Open the role. On **Trust relationships**, the principal is `lambda.amazonaws.com` and the action is `sts:AssumeRole`.
6. On **Permissions**, the logs policy is the only permissions policy.

**Expected:** the role exists and the trust policy names Lambda, not a user.

**If the name is taken:** delete the old role if it has no function attached, or reuse it if the trust policy is already Lambda.

### 3. Leave these uncreated

Do not create a NAT gateway. Do not create a VPC endpoint. The private route table shows the path you would add later: `0.0.0.0/0` to a NAT gateway, or a prefix-list route to an S3 gateway endpoint.

## When you are done

1. IAM → role `sample-create-order-role` → delete, unless a later example will reuse it the same day. Remove the attached policy if the console asks.
2. VPC → select `sample-orders-vpc` → **Actions** → **Delete VPC**. Confirm deletion of subnets and the internet gateway when offered.
3. If delete is blocked, detach the internet gateway, delete subnets, delete route tables that are not the main table, then delete the VPC.
4. Confirm you did not leave a NAT gateway. NAT gateways are under VPC → NAT gateways. The list should be empty.

You do not need `sample-lambda-sg` to understand the rules. If you create `sample-aurora-sg` to practice, delete it in this cleanup. The CIDRs and the public versus private route are the check. Renaming wizard subnets is optional.

## What this costs

A VPC, subnets, route tables, an internet gateway, and an IAM role do not have an hourly charge. A NAT gateway does. An interface endpoint does. Check both lists before you leave the account.
