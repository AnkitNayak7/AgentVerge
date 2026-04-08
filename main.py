from fastapi import FastAPI
import uvicorn

from agents.agentverge.config import APP_NAME, ROOT_AGENT_NAME

app = FastAPI()


@app.get("/")
def home():
    return {
        "status": "ok",
        "message": f"{ROOT_AGENT_NAME} is ready.",
        "service": APP_NAME,
    }


@app.get("/run")
def run_agent():
    return {
        "status": "success",
        "message": f"Launch {ROOT_AGENT_NAME} from the ADK web UI.",
    }


def main():
    print(f"{ROOT_AGENT_NAME} is ready.")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
