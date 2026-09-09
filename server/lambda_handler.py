"""AWS Lambda entry point: wraps the existing FastAPI app (server/app.py) for
Lambda + a Function URL via Mangum. Not used by local `uvicorn` runs - those
still target server.app:app directly. Deployed as clubapply_strands.server.lambda_handler.handler.
"""

from __future__ import annotations

from mangum import Mangum

from .app import app

handler = Mangum(app)
