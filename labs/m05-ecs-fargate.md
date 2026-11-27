# Module 5 lab: One Fargate packing task

**Time:** 35 minutes  
**Region:** ap-south-1  
**You will create:** cluster `sample-orders`, service `sample-packing`, security group `sample-fargate-sg`  
**You will not create:** a load balancer, a NAT gateway, or an EC2 container instance

If the instructor already started `sample-packing`, use that service for steps 4 and 5 and do not start a second one.

## 1. Create the cluster

1. Set the region to **ap-south-1**.
2. Open **ECS** → **Clusters** → **Create cluster**.
3. Name: `sample-orders`. Infrastructure: **AWS Fargate** only.

## 2. Create the task definition

1. Open **Task definitions** → **Create new task definition**.
2. Family: `sample-packing`. Launch type: **Fargate**.
3. CPU **0.25 vCPU**. Memory **0.5 GB**.
4. Task execution role: create `ecsTaskExecutionRole` if it does not exist. Task role: none.
5. Container name: `packing`.
6. Image: `public.ecr.aws/docker/library/nginx:stable`.
7. Container port: **80**.
8. Turn on CloudWatch logs. Log group: `/ecs/sample-packing`. Region: `ap-south-1`.
9. Create the definition. It should be revision **1**.

## 3. Create the security group and the service

1. In the **default VPC**, create a security group named `sample-fargate-sg`.
2. Add no inbound rules. Allow outbound TCP **443** to `0.0.0.0/0`.
3. Create an ECS service on cluster `sample-orders`.
   - Task definition `sample-packing` revision 1.
   - Service name `sample-packing`.
   - Desired tasks: **1**.
   - VPC: default VPC. Subnet: a **public** subnet.
   - Security group: `sample-fargate-sg`.
   - Public IP: **on**.
   - Load balancer: **none**.
4. Wait until the task status is **Running**.

## 4. Read one log line

1. Open CloudWatch log group `/ecs/sample-packing`.
2. Open the latest stream and copy one line that shows the container started.
3. If the task stops with a pull error, tell the instructor. Do not create a NAT gateway.

## 5. Point at rollback

1. With the instructor, open the task definition and note revision 1.
2. Find the service update control where a later revision would be selected.
3. Write one sentence: rollback means updating `sample-packing` to an older revision, not editing the running container.

## 6. Cleanup

1. Delete the service `sample-packing` and wait until **no tasks are running**.
2. Delete the cluster `sample-orders`.
3. Delete `sample-fargate-sg` after the task network interface is gone.
4. Delete log group `/ecs/sample-packing`.

## Done when

- You saw a running task and one log line, or you watched the instructor’s shared service do both.
- The service is deleted and the running task count is zero.
