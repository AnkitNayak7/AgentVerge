from google.adk.agents.llm_agent import LlmAgent

from ..config import DEFAULT_MODEL, ROOT_AGENT_NAME
from ..prompts import load_prompt
from .calendar_agent import calendar_manager
from .research_agent import research_agent
from .tasks_agent import tasks_manager

root_agent = LlmAgent(
    name=ROOT_AGENT_NAME,
    model=DEFAULT_MODEL,
    description="AgentVerge is the only web-visible root agent and delegates to internal specialists.",
    sub_agents=[calendar_manager, tasks_manager, research_agent],
    instruction=load_prompt("orchestrator.md"),
)
