from google.adk.apps import App

from .agents.orchestrator import root_agent
from .config import APP_NAME

adk_app = App(name=APP_NAME, root_agent=root_agent)
