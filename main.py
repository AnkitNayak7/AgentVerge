import os
import asyncio
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.join(BASE_DIR, "agents")

app = FastAPI()
adk_loaded = False


async def load_adk():
    """
    Load Google ADK in background so Cloud Run can bind PORT immediately
    """
    global adk_loaded
    try:
        adk_app = get_fast_api_app(
            agents_dir=AGENTS_DIR,
            allow_origins=["*"],
            web=True,   # keep web UI
        )
        app.mount("/", adk_app)
        adk_loaded = True
        print("✅ ADK loaded successfully")
    except Exception as e:
        print("❌ ADK failed to load:", e)


@app.on_event("startup")
async def startup_event():
    """
    Cloud Run SAFE:
    - Do NOT block startup
    - Kick off ADK init in background
    """
    asyncio.create_task(load_adk())


@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "service": "agentverge",
        "adk_loaded": adk_loaded,
    }
