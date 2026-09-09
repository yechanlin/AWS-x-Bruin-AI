# Deploying ClubApply to AWS (free tier)

> The active frontend now uses **Amplify Hosting**. See [Amplify deployment](AMPLIFY.md)
> for its live URL and redeployment steps. The S3 frontend instructions below
> describe the older alternative. Free-tier coverage for this account is unverified.

Architecture: the FastAPI backend runs as a **Lambda container image** behind a
**Function URL**; the React frontend is a static build in an **S3 bucket**.

Why this combination: Lambda's free tier is *permanent* (1M requests + 400,000
GB-seconds of compute per month, no 12-month expiry), and an S3-hosted React
build is a few MB, so storage/transfer costs round to cents even outside any
free tier. Nothing here depends on the 12-month new-account free tier.

**This is not a $0 guarantee.** At personal-project traffic it's effectively
free, but heavy traffic, a runaway loop, or model usage will cost money. Read
"Cost and safety guardrails" at the bottom *before* going public.

---

## Prerequisites

1. An AWS account.
2. AWS CLI installed and configured:
   ```sh
   brew install awscli          # macOS
   aws configure                # paste your IAM access key + secret, set region (e.g. us-east-1)
   aws sts get-caller-identity  # should print your account ID
   ```
3. Docker running (Docker Desktop on macOS).
4. Your provider API key(s) — the same ones in your local `.env`.

Note your **account ID** (from `get-caller-identity`) and chosen **region**
(e.g. `us-east-1`); both are used throughout.

---

## Part 1 — Backend (one-time setup)

### 1.1 Create the ECR repository (stores the container image)

```sh
aws ecr create-repository --repository-name clubapply-backend --region us-east-1
```

### 1.2 Create the Lambda execution role

```sh
aws iam create-role --role-name clubapply-lambda-role \
  --assume-role-policy-document '{
    "Version":"2012-10-17",
    "Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]
  }'

aws iam attach-role-policy --role-name clubapply-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

**If you want to use Bedrock** (instead of an OpenAI/Gemini key), also grant it
model access — this is the clean part of running on AWS, since Lambda gets
credentials from its role and you never store an AWS key anywhere:

```sh
aws iam put-role-policy --role-name clubapply-lambda-role \
  --policy-name bedrock-invoke \
  --policy-document '{
    "Version":"2012-10-17",
    "Statement":[{"Effect":"Allow","Action":["bedrock:InvokeModel"],"Resource":"*"}]
  }'
```
(Bedrock also requires enabling model access once, per-region, in the Bedrock console.)

### 1.3 Build and push the first image

```sh
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1

aws ecr get-login-password --region $REGION \
  | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

docker build --platform linux/amd64 --provenance=false --sbom=false -t clubapply-backend .
docker tag clubapply-backend:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/clubapply-backend:latest
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/clubapply-backend:latest
```

Two flags matter here. `--platform linux/amd64` because Lambda runs x86_64 by
default and Apple Silicon would otherwise build arm64. `--provenance=false
--sbom=false` because Docker Desktop's buildx otherwise pushes an OCI *manifest
list*, which Lambda rejects with "The image manifest, config or layer media type
for the source image is not supported.".

### 1.4 Create the Lambda function

```sh
aws lambda create-function \
  --function-name clubapply-backend \
  --package-type Image \
  --code ImageUri=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/clubapply-backend:latest \
  --role arn:aws:iam::$ACCOUNT_ID:role/clubapply-lambda-role \
  --timeout 60 \
  --memory-size 1024 \
  --region $REGION
```

`--timeout 60` matters: a full run crawls a website *and* makes several model
calls, which takes well over Lambda's 3-second default. `--memory-size 1024`
also buys proportionally more CPU, which meaningfully cuts cold-start time.

### 1.5 Set the API keys as environment variables

Never bake these into the image — `.env` is excluded via `.dockerignore`.

```sh
aws lambda update-function-configuration \
  --function-name clubapply-backend \
  --environment "Variables={OPENAI_API_KEY=sk-...,LLM_TIMEOUT_SECONDS=20}" \
  --region $REGION
```

Add `GEMINI_API_KEY`, or `LLM_PROVIDER=bedrock` (no key needed — it uses the
role from 1.2), as you like. All the fallback behaviour from `.env.example`
applies identically here.

### 1.6 Create the Function URL (the public HTTPS endpoint)

```sh
aws lambda create-function-url-config \
  --function-name clubapply-backend \
  --auth-type NONE \
  --region $REGION

aws lambda add-permission \
  --function-name clubapply-backend \
  --statement-id FunctionURLAllowPublicAccess \
  --action lambda:InvokeFunctionUrl \
  --principal "*" \
  --function-url-auth-type NONE \
  --region $REGION

aws lambda add-permission \
  --function-name clubapply-backend \
  --statement-id FunctionURLAllowPublicInvoke \
  --action lambda:InvokeFunction \
  --principal "*" \
  --invoked-via-function-url \
  --region $REGION
```

This prints a `FunctionUrl` like `https://abc123.lambda-url.us-east-1.on.aws/`.
Save it — the frontend build needs it. Verify:

```sh
curl https://abc123.lambda-url.us-east-1.on.aws/health
# {"ok":true,"model_mode":"configured"}
```

---

## Part 2 — Frontend (one-time setup)

### 2.1 Create the bucket and enable static website hosting

Bucket names are globally unique, so pick your own.

```sh
BUCKET=clubapply-frontend-yourname

aws s3 mb s3://$BUCKET --region $REGION
aws s3 website s3://$BUCKET --index-document index.html --error-document index.html
```

### 2.2 Allow public reads

```sh
aws s3api put-public-access-block --bucket $BUCKET \
  --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

aws s3api put-bucket-policy --bucket $BUCKET --policy "{
  \"Version\":\"2012-10-17\",
  \"Statement\":[{\"Sid\":\"PublicRead\",\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"s3:GetObject\",\"Resource\":\"arn:aws:s3:::$BUCKET/*\"}]
}"
```

### 2.3 Build and upload

```sh
./scripts/deploy-frontend.sh $BUCKET https://abc123.lambda-url.us-east-1.on.aws
```

Live at `http://$BUCKET.s3-website-$REGION.amazonaws.com`.

### 2.4 Lock CORS to that origin

```sh
aws lambda update-function-configuration \
  --function-name clubapply-backend \
  --environment "Variables={OPENAI_API_KEY=sk-...,ALLOWED_ORIGINS=http://$BUCKET.s3-website-$REGION.amazonaws.com}" \
  --region $REGION
```

`update-function-configuration` **replaces** the whole environment block, so
repeat every variable you want to keep.

---

## Redeploying after code changes

```sh
./scripts/deploy-backend.sh $ACCOUNT_ID $REGION clubapply-backend clubapply-backend
./scripts/deploy-frontend.sh $BUCKET https://abc123.lambda-url.us-east-1.on.aws
```

---

## Cost and safety guardrails

A public Function URL with `--auth-type NONE` means **anyone who finds the URL
can trigger model calls billed to your API key**. `ALLOWED_ORIGINS` only
restricts browsers; `curl` ignores CORS entirely. Before sharing it widely:

1. **Cap Lambda concurrency** so a burst can't fan out:
   ```sh
   aws lambda put-function-concurrency --function-name clubapply-backend \
     --reserved-concurrent-executions 5 --region $REGION
   ```
2. **Set a spending limit at your model provider** (OpenAI dashboard → Billing →
   limits). This is the real backstop, since it's the one cost that scales with
   abuse rather than staying in a free tier.
3. **Set an AWS Budgets alert** so you find out from an email rather than an invoice.
4. Consider requiring a shared secret header if this is only for demos — the
   app has no authentication of any kind today.

Still open from the project roadmap and **not** solved by deploying:
no auth, no rate limiting, no per-user upload scoping, and no SSRF protection
on the crawler (it will fetch whatever URL it's handed).
