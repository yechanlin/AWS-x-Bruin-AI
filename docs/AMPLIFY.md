# ClubApply on Amplify Hosting

## Active GitHub deployment

Website: https://main.d8qdpc5eyzotl.amplifyapp.com
App ID: d8qdpc5eyzotl
Repository: https://github.com/yechanlin/AWS-x-Bruin-AI
Branch: main; automatic builds enabled.

Push frontend changes to main to trigger Amplify. The repository amplify.yml
builds client with npm ci and npm run build, then publishes client/build.
The new website origin is allowed by the Lambda backend. Verified deployment
SUCCEED and HTTP 200 CORS preflight for POST requests. Backend Python changes
still require the separate Lambda deployment script.

In the AWS console, use Hosting > Build settings for build configuration,
Hosting > Environment variables for REACT_APP_API_URL, and the main branch
deployment page for build logs and status.

## Previous manual deployment

The following app remains available as the earlier manual deployment.

Frontend: https://main.d30icqn5v2iewm.amplifyapp.com
Backend: https://oktccipydmib776oy23hsjmeem0zzvob.lambda-url.us-east-1.on.aws
Region: us-east-1
Amplify app ID: d30icqn5v2iewm
Production branch: main

The React files are hosted by Amplify; the browser calls the existing FastAPI
backend on Lambda. ECR stores the backend container image.

## Redeploy the frontend

From the repository root:

```sh
(cd client && REACT_APP_API_URL=https://oktccipydmib776oy23hsjmeem0zzvob.lambda-url.us-east-1.on.aws npm run build)
python3 scripts/publish-amplify.py d30icqn5v2iewm
```

The script uploads built files (excluding source maps) and starts a deployment.
It prints the job ID, not a final success result. Check completion with:

```sh
aws amplify get-job --app-id d30icqn5v2iewm --branch-name main --job-id JOB_ID --region us-east-1 --query 'job.summary.status'
```

This is a manual deployment of the local checkout. GitHub auto-deployment is
not configured. Committing and connecting the repository can be done later,
with `client` as the app root and REACT_APP_API_URL as a build variable.
Changing an Amplify variable alone does not change an already-built manual ZIP.

## Backend connection

Lambda's ALLOWED_ORIGINS includes the frontend HTTPS origin. Existing backend
environment variables were preserved. CORS is handled by FastAPI, not duplicated
in Function URL configuration. CORS controls browser access, not authentication.
The Function URL has both lambda:InvokeFunctionUrl and lambda:InvokeFunction
permissions; the latter is restricted by lambda:InvokedViaFunctionUrl.

## Billing and recovery

The free-plan API returned ResourceNotFoundException for this account; this does
not establish free-tier eligibility or a zero bill. Amplify, Lambda, ECR, logs,
and model providers have separate usage charges/allowances. No billing alert was
created. Check Billing in the AWS console for actual credits and charges.

For a bad frontend release, rebuild a known-good checkout and publish it with the
same command. Keep backend changes separate from frontend publishing.
