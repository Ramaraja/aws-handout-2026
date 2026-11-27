# Module 1 lab: Region, budget, and the Sample Orders map

**Time:** 35 minutes  
**Region:** ap-south-1 (Asia Pacific, Mumbai)  
**You will create:** one monthly cost budget, if your user can open Billing. Nothing else.

Work in the training account only. Do not launch an EC2 instance, a database, or a bucket today.

## 1. Set the region

1. Sign in to the AWS console.
2. Open the region selector in the top bar.
3. Choose **Asia Pacific (Mumbai) ap-south-1**.
4. Write down the region code you see: `ap-south-1`.

If the selector is already on Mumbai, leave it there.

## 2. Read the account id

1. Search for **IAM** and open the service.
2. On the dashboard, find the account id. It is 12 digits.
3. Write it down. Module 8 uses it in a bucket name. Do not create an access key on this page.

## 3. Create the training budget

If a budget named `sample-orders-training` is already in the account, open it, confirm the amount is 20 USD, and skip to step 4.

1. Search for **Budgets**.
2. Create a **cost budget**.
3. Use a monthly period and a budgeted amount of **20** USD.
4. Name it `sample-orders-training`.
5. Add email alerts at **80** percent and at **100** percent of the budgeted amount. Use the instructor’s email if you are sharing one console. Use your own email only if the instructor told you to.
6. Save the budget.
7. Confirm the budget is listed and that current spend is visible.

If Billing says you are not allowed, stop this step and tell the instructor. Finish step 4 anyway.

## 4. Place Sample Orders on four layers

On paper or in a document, make four headings. Under each heading, write the resource name from the list. Use each name once.

Names:

- `sample-orders-api`
- `sample-create-order`
- `sample-packing`
- `order-events`
- `inventory-queue`
- `notify-queue`
- `sample-orders-db`
- `sample-orders-invoices-ACCOUNTID` (use the account id from step 2)

Headings:

- Entry
- Compute
- Integration
- Data

Then write two sentences:

1. Which of these will exist in `ap-south-1` as a regional resource, and which identity service is global instead.
2. For Amazon Aurora later in the course, name one thing AWS operates and one thing Sample Orders still has to decide.

## 5. Stop

Do not click Create on any other service. Leave the budget in the account.

## Done when

- The console region is ap-south-1.
- You have the 12-digit account id written down.
- The budget exists, or the instructor has confirmed you lack billing permission and the budget already exists.
- Your four-layer list uses the names above, and your two sentences are written.
