#!/usr/bin/env bash
# Rebuilds the backend Docker image, pushes it to ECR, and updates the Lambda
# function to use it. Assumes the ECR repo and Lambda function already exist
# (one-time setup - see docs/DEPLOYMENT.md). Needs AWS credentials (aws configure)
# and Docker running.
#
# Usage:
#   ./scripts/deploy-backend.sh <aws-account-id> <region> <ecr-repo-name> <lambda-function-name>
#   ./scripts/deploy-backend.sh 123456789012 us-east-1 clubapply-backend clubapply-backend
set -euo pipefail

ACCOUNT_ID="${1:?Usage: deploy-backend.sh <account-id> <region> <ecr-repo-name> <lambda-function-name>}"
REGION="${2:?Usage: deploy-backend.sh <account-id> <region> <ecr-repo-name> <lambda-function-name>}"
REPO_NAME="${3:?Usage: deploy-backend.sh <account-id> <region> <ecr-repo-name> <lambda-function-name>}"
FUNCTION_NAME="${4:?Usage: deploy-backend.sh <account-id> <region> <ecr-repo-name> <lambda-function-name>}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME"

echo "Building image..."
# --provenance/--sbom=false are required: buildx otherwise pushes an OCI
# manifest list, which Lambda rejects with "image manifest ... not supported".
docker build --platform linux/amd64 --provenance=false --sbom=false -t "$REPO_NAME" "$REPO_ROOT"

echo "Logging in to ECR..."
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

echo "Tagging and pushing..."
docker tag "$REPO_NAME:latest" "$ECR_URI:latest"
docker push "$ECR_URI:latest"

echo "Updating Lambda function code..."
aws lambda update-function-code \
  --function-name "$FUNCTION_NAME" \
  --image-uri "$ECR_URI:latest" \
  --region "$REGION"

echo "Done. Lambda is updating - check status with:"
echo "  aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query 'Configuration.LastUpdateStatus'"
