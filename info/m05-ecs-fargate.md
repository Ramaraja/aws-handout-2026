# Containers and ECS Fargate

**Handout.** Region: **ap-south-1** (Mumbai).

You run the packing service as a container. You create cluster `sample-orders`, service and task family `sample-packing`, and security group `sample-fargate-sg`.

## Goals

By the end of this handout you can explain:

1. How an image, a container, a task definition, and a service differ.
2. How to run one Fargate task for `sample-packing` without managing an EC2 instance.
3. How to place the task on a public subnet with a task execution role and a CloudWatch log driver.
4. How a rolling update is a new task-definition revision, and a rollback is returning the service to the previous revision.

## Container fundamentals

An **image** is the packaged application: filesystem, runtime, and the command to start. The packing example uses the public image `public.ecr.aws/docker/library/nginx:stable`. It is a stand-in. The real packing process would be Sample’s own image in Amazon ECR. You do not need a local Docker install to run this example.

A **container** is a running instance of that image. It has a process, environment variables, and stdout. When the process exits, the container stops. Anything written only to the container’s disk is gone. Packing state belongs in Aurora, not in the container filesystem.

A registry stores images. Amazon ECR is the private registry in the account. Public ECR is where this example pulls from. Pulling requires a network path to the registry. That constraint drives the subnet choice.

Why a container when Lambda already accepts the order:

- `sample-create-order` is a short request.
- `sample-packing` is a service that stays running, may hold a connection to Aurora, and is deployed as a versioned image. Fargate is the compute for that shape. You still do not patch a server.

## Amazon ECS and Fargate

| Piece | Sample Orders name | What it is |
| --- | --- | --- |
| Cluster | `sample-orders` | A logical grouping. On Fargate it does not contain servers you manage. |
| Task definition | family `sample-packing` | The blueprint: image, CPU, memory, role, logging. Revisions are immutable. Revision 2 does not edit revision 1. |
| Task | one running copy | A running blueprint. Desired count 1 means one task. |
| Service | `sample-packing` | Keeps the desired count running. If a task stops, the service starts another. |

**Fargate** is the launch type that does not ask you for an EC2 capacity provider, an AMI, or a scaling group. You set CPU and memory. This example uses **0.25 vCPU** and **0.5 GB**. That is the smallest size. It is enough for nginx. It is not a performance test.

The EC2 launch type would put the same task definition on instances you patch and pay for while they are up. Sample’s packing service does not use it. ECS is the orchestrator. Fargate is the capacity.

There is no load balancer in this example. An Application Load Balancer adds an hourly charge and a target group you do not need in order to read a log line. The service, in the story, later reaches Aurora on a private connection. Here it only needs to start and log.

## Networking, roles, and logs

Fargate tasks use **awsvpc**. Each task gets its own elastic network interface and its own security group.

The image pull fails in a private subnet with no NAT gateway. This example:

- Uses the **default VPC**, which has an internet gateway and public subnets.
- Assigns a **public IP** so the task can reach the registry and CloudWatch Logs.
- Uses security group `sample-fargate-sg` with **no inbound rules** and outbound TCP **443** to `0.0.0.0/0`.

No inbound rule is correct. Nothing on the internet should open port 80 on the packing task. You are reading logs, not browsing the nginx welcome page.

Two roles:

- The **task execution role** is used by the ECS agent: pull the image and write logs. The managed policy is `AmazonECSTaskExecutionRolePolicy`. The console can create `ecsTaskExecutionRole`.
- The **task role** is what the application code uses, the same idea as `sample-create-order-role`. nginx does not call AWS APIs. Leave the task role empty. When packing reads Aurora, this role is where database auth belongs, not in a password baked into the image.

Logs use the `awslogs` driver. The log group is `/ecs/sample-packing` in `ap-south-1`. The container must write to stdout or stderr. The nginx image does. A file under `/var/log` inside the container does not appear in CloudWatch unless the process also writes it to the console.

Environment variables and secrets configure the image without rebuilding it. A revision can add `PACKING_MODE=demo`. Secrets Manager is the right place for a password. An environment variable in the task definition is visible to anyone who can read the task definition. Do not put the Aurora password there.

## Deployment and rollback

A service deployment replaces tasks. The simple strategy ECS uses here is a **rolling update**. Minimum healthy percent and maximum percent decide how many extra tasks may run during the swap. With desired count 1, a rolling update starts the new task, then stops the old one, if the maximum percent allows 200. The unit of deploy is a **new revision**.

Rollback is updating the service back to the previous task-definition revision. Revision 1 is still there. You do not roll back by editing a running container.

The deployment circuit breaker, if turned on, notices a revision that cannot reach steady state and can roll the service back. Leave it as a named control. A bad image is how you strand a service. Use the revision selector instead of forcing a failed pull.

A second cluster, a blue/green CodeDeploy pipeline, and a multi-region deploy are real options and are outside this example. Recovering the service in another region means running the same task definition there.

## In the console

### 1. Create the cluster

1. Region **ap-south-1**. **ECS** → **Clusters** → **Create cluster**.
2. Name `sample-orders`. Infrastructure: **AWS Fargate** only. Do not add an EC2 capacity provider.
3. Create the cluster.

### 2. Create the task definition

1. **Task definitions** → **Create**.
2. Family `sample-packing`. Launch type **Fargate**.
3. CPU **0.25 vCPU**. Memory **0.5 GB**.
4. Task execution role: create or select `ecsTaskExecutionRole`. Task role: **None**.
5. Container name `packing`. Image `public.ecr.aws/docker/library/nginx:stable`.
6. Port mapping **80** TCP. This does not open the port to the world. The security group does that, and this group will not.
7. Log collection: **Amazon CloudWatch** turned on. Log group `/ecs/sample-packing`. Region `ap-south-1`.
8. Create the definition. It is revision **1**.

### 3. Create the security group and the service

1. **EC2** or **VPC** → security groups → create `sample-fargate-sg` in the **default VPC**. Outbound HTTPS 443 to `0.0.0.0/0`. No inbound rules.
2. ECS → cluster `sample-orders` → **Create service**.
3. Launch type Fargate. Task definition `sample-packing` revision 1. Service name `sample-packing`. Desired count **1**.
4. Networking: default VPC, one **public** subnet, security group `sample-fargate-sg`, **public IP turned on**.
5. Load balancer: **none**.
6. Create the service. Wait until the task is **Running**.

**Expected:** one running task. Within a couple of minutes the log group `/ecs/sample-packing` has a stream, and the stream contains an nginx start line.

**If the task stops immediately:** open the stopped task and read the reason. `CannotPullContainerError` means the task had no public IP or the subnet was private. Recreate the service with a public subnet and a public IP. Do not fix this by creating a NAT gateway.

**If the task runs and the log group is empty:** the log driver was not saved on the container. Create revision 2 with logging enabled and update the service.

### 4. See rollback without a bad deploy

1. Create a new revision of `sample-packing`. Add an environment variable `PACKING_MODE` = `demo`. Save. That is revision **2**.
2. Update the service to revision 2.
3. Open **Update service** again. Rollback is choosing revision **1** and updating. The previous revision is the rollback artifact.

## When you are done

1. Service `sample-packing` → **Delete service**. Force delete if offered. Desired count goes to 0.
2. Wait until no tasks are running. A task left running is the charge.
3. Delete the cluster `sample-orders`.
4. Delete security group `sample-fargate-sg` after the network interface is gone. If delete fails, the task ENI is still attached. Wait one minute and retry.
5. Delete log group `/ecs/sample-packing`.
6. Task definitions do not bill. Deregister revisions if you want a clean list.

Confirm **ECS** → cluster → tasks is empty, and **EC2** → network interfaces has no leftover `fargate` interface in use.

One service is enough. The success check is a log line, not a browser tab on port 80. Do not add an Application Load Balancer or a NAT gateway.

## What this costs

One task at 0.25 vCPU and 0.5 GB for the length of this exercise is a small charge. It becomes a real charge if the service is left overnight. Delete the service and watch the running task count hit zero. This example has no load balancer and no NAT gateway.
