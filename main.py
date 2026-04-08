import os
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.join(BASE_DIR, "agents")

# ✅ Create a minimal FastAPI app immediately
app = FastAPI()


@app.on_event("startup")
def startup_event():
    """
    IMPORTANT:
    - Do NOT do heavy work at import time in Cloud Run
    - Initialize ADK only AFTER the server process starts
    """
    adk_app = get_fast_api_app(
        agents_dir=AGENTS_DIR,
        allow_origins=["*"],
        web=True,
    )

    # Mount ADK app at root
    app.mount("/", adk_app)


@app.get("/healthz")
def healthz():
    """
    Lightweight health check for Cloud Run
    """
    return {"status": "ok", "service": "agentverge"}
