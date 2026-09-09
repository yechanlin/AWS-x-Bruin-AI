#!/usr/bin/env bash
# Builds the React app pointed at a deployed backend URL and syncs it to an S3
# bucket configured for static website hosting. Needs AWS credentials
# (aws configure) and the bucket to already exist - see docs/DEPLOYMENT.md.
#
# Usage:
#   ./scripts/deploy-frontend.sh <s3-bucket-name> <backend-url>
#   ./scripts/deploy-frontend.sh clubapply-frontend https://abc123.lambda-url.us-east-1.on.aws
set -euo pipefail

BUCKET="${1:?Usage: deploy-frontend.sh <s3-bucket-name> <backend-url>}"
API_URL="${2:?Usage: deploy-frontend.sh <s3-bucket-name> <backend-url>}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT/client"

echo "Building React app with REACT_APP_API_URL=$API_URL ..."
REACT_APP_API_URL="$API_URL" npm run build

echo "Syncing build/ to s3://$BUCKET ..."
aws s3 sync build/ "s3://$BUCKET" --delete

echo "Done. If this bucket has static website hosting enabled, it's live at:"
echo "  http://$BUCKET.s3-website-<region>.amazonaws.com"
