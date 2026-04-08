import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from google.adk.cli.fast_api import get_fast_api_app

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.join(BASE_DIR, "agents")

adk_loaded = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global adk_loaded

    print("🚀 App starting...")

    try:
        adk_app = get_fast_api_app(
            agents_dir=AGENTS_DIR,
            allow_origins=["*"],
            web=True,
        )
        app.mount("/", adk_app)
        adk_loaded = True
        print("✅ ADK loaded successfully")
    except Exception as e:
        print("❌ ADK failed to load:", e)

    yield

    print("🛑 App shutting down...")


app = FastAPI(lifespan=lifespan)


@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "service": "agentverge",
        "adk_loaded": adk_loaded,
    }
