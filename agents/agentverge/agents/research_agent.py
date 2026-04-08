from google.adk.agents import SequentialAgent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import AgentTool, google_search

from ..config import DEFAULT_MODEL
from ..prompts import load_prompt

planner = LlmAgent(
    name="research_planner",
    model=DEFAULT_MODEL,
    instruction="""
You are a research planning specialist.

Break the user's request into exactly three distinct research themes.
Return a practical plan the downstream research pipeline can execute clearly.
""".strip(),
)

researcher = LlmAgent(
    name="researcher",
    model=DEFAULT_MODEL,
    tools=[google_search],
    instruction="""
You are the research execution specialist.

Research the assigned topic step-by-step, use Google Search when needed,
and gather the most relevant facts before handing off to the synthesizer.
""".strip(),
)

synthesizer = LlmAgent(
    name="synthesizer",
    model=DEFAULT_MODEL,
    instruction="""
You are the synthesis specialist.

Combine the research findings into one cohesive, well-structured answer
that directly addresses the user's request.
""".strip(),
)

execution_pipeline = SequentialAgent(
    name="research_execution_pipeline",
    description="Runs the research and synthesis stages in sequence.",
    sub_agents=[researcher, synthesizer],
)

research_agent = LlmAgent(
    name="research_manager",
    model=DEFAULT_MODEL,
    description="Handles general research, information gathering, and synthesized summaries.",
    tools=[AgentTool(planner)],
    sub_agents=[execution_pipeline],
    instruction=(
        load_prompt("research_agent.md")
        + "\n\n"
        + """
Workflow:
1. Use the research_planner tool to produce a detailed three-theme research plan.
2. Pass that completed plan to the research_execution_pipeline sub-agent.
3. Return the synthesized final answer from the pipeline to the user.
""".strip()
    ),
)
