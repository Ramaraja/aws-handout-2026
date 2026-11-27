# Module 2 lab: VPC without NAT, and a Lambda role

**Time:** 35 minutes  
**Region:** ap-south-1  
**You will create:** `sample-orders-vpc` and `sample-create-order-role`  
**You will not create:** a NAT gateway, a VPC endpoint, or an EC2 instance

## 1. Create the VPC

1. Set the region selector to **Asia Pacific (Mumbai) ap-south-1**.
2. Open **VPC** → **Create VPC** → **VPC and more**.
3. Set the IPv4 CIDR to `10.0.0.0/16`.
4. Use **2** Availability Zones, **2** public subnets, and **2** private subnets.
5. Set **NAT gateways** to **None**.
6. Set **VPC endpoints** to **None**.
7. Enable DNS hostnames.
8. Name the VPC `sample-orders-vpc`. If the wizard asks for a project prefix instead of a VPC name, use `sample-orders` and rename the VPC to `sample-orders-vpc` after it exists.
9. Create the VPC.

## 2. Check the routes

1. Open the route tables created for this VPC.
2. Find the table associated with the public subnets (`10.0.1.0/24` and `10.0.2.0/24`). Confirm a route `0.0.0.0/0` whose target is an internet gateway.
3. Find the table associated with the private subnets (`10.0.11.0/24` and `10.0.12.0/24`). Confirm there is **no** route to `0.0.0.0/0`.
4. Write one sentence: why the private table is the right place for `sample-orders-db`.

## 3. Create the role

1. Open **IAM** → **Roles** → **Create role**.
2. Trusted entity: **AWS service** → **Lambda**.
3. Attach only **AWSLambdaBasicExecutionRole**.
4. Name: `sample-create-order-role`.
5. Open the role → **Trust relationships**. Confirm the service principal is `lambda.amazonaws.com`.

## 4. Cleanup

Delete what you created. The next module can make the role again.

1. Delete the role `sample-create-order-role`.
2. Delete the VPC `sample-orders-vpc`, including the subnets and internet gateway the console offers to delete with it.
3. Open **NAT gateways** and confirm the list is empty.
4. Open **Endpoints** and confirm you did not add one.

## Done when

- You saw a public default route and a private table without one.
- The role trust policy names Lambda, and the only permissions policy is basic logging.
- The VPC, the role, and any accidental NAT gateway are gone.
