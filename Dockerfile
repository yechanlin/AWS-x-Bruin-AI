# Lambda container image for the ClubApply Strands backend.
#
# The repo root is a flat Python package (pyproject.toml maps "clubapply_strands"
# to "."), so the source is copied into ${LAMBDA_TASK_ROOT}/clubapply_strands/
# to mirror that same import layout inside the image. The handler is
# clubapply_strands.server.lambda_handler.handler (see that file - it wraps
# server/app.py's FastAPI app with Mangum; nothing about the app itself changes).
#
# Build (from the repo root):
#   docker build -t clubapply-backend .
# Local smoke test (starts the AWS Lambda Runtime Interface Emulator on :9000):
#   docker run --rm -p 9000:8080 --env-file .env clubapply-backend
#   curl "http://localhost:9000/2015-03-31/functions/function/invocations" \
#     -d '{"version":"2.0","rawPath":"/health","requestContext":{"http":{"method":"GET","path":"/health"}}}'

FROM public.ecr.aws/lambda/python:3.12

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY __init__.py schemas.py orchestrator.py logging_config.py main.py "${LAMBDA_TASK_ROOT}/clubapply_strands/"
COPY agents "${LAMBDA_TASK_ROOT}/clubapply_strands/agents"
COPY tools "${LAMBDA_TASK_ROOT}/clubapply_strands/tools"
COPY server "${LAMBDA_TASK_ROOT}/clubapply_strands/server"

# Secrets come from Lambda's own environment configuration, never baked into
# the image - .env is excluded via .dockerignore. load_dotenv() in app.py
# simply no-ops here since no .env file exists in the image.
CMD ["clubapply_strands.server.lambda_handler.handler"]
