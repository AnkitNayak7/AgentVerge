# AgentVerge

This repository is structured around a single Google ADK app named `AgentVerge`.

`AgentVerge` is the only top-level app intended to appear in the ADK web UI. Calendar, Tasks, and Research are implemented as internal sub-agents beneath that root orchestrator.

## Prerequisites

- [Python 3.13+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) (Python package and environment manager)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd AgentVerge
   ```

2. **Install dependencies using uv:**
   ```bash
   uv sync
   ```

## Environment Setup

You need the Gemini model key and Google OAuth settings used by the sub-agents.

1. Get an API key from [Google AI Studio](https://aistudio.google.com/).
2. Copy the sample environment file:
   ```bash
   cp sample.env .env
   ```
3. Edit `.env` and provide the values needed by the app, including:
   - `GOOGLE_API_KEY`
   - `OAUTH_CLIENT_ID`
   - `OAUTH_CLIENT_SECRET`
   - optional `APP_TIMEZONE`
4. In Google Cloud, make sure the OAuth redirect URI matches the ADK Web URL you actually use.
   - If you run `uv run adk web agents --port 8000`, add `http://127.0.0.1:8000/dev-ui/` as an authorized redirect URI.
   - If you use a different port, change the redirect URI to match that exact port.

*Note: The `.env` file is ignored by Git to keep your API keys secure.*

## Project Layout

```text
agents/
\-- agentverge/
    +-- agent.py
    +-- main.py
    +-- config.py
    +-- prompts/
    +-- agents/
    +-- tools/
    +-- state/
    +-- services/
```

## Running AgentVerge

### 1. Run the FastAPI entrypoint
```bash
uv run python main.py
```

### 2. Run AgentVerge in ADK CLI
```bash
uv run adk run agents/agentverge
```

### 3. Run AgentVerge in ADK Web
```bash
uv run adk web agents --port 8000
```
Then open `http://localhost:8000/dev-ui/`.

If Google Calendar or Google Tasks actions do not prompt for sign-in or fail immediately, verify that the OAuth redirect URI in Google Cloud exactly matches `http://127.0.0.1:8000/dev-ui/` for this command.

With the legacy agent folders moved out of top-level discovery, the web UI should surface only `AgentVerge` as the main app.
