from google.adk.agents import SequentialAgent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import google_search

from ..config import DEFAULT_MODEL
from ..prompts import load_prompt

researcher = LlmAgent(
    name="researcher",
    model=DEFAULT_MODEL,
    tools=[google_search],
    instruction=(
        """
You are the research execution specialist.

The approved research plan is:
{research_plan}

Execute that plan thoroughly using Google Search when needed.
Organize your findings by the same three themes from the plan.
For each theme, capture the most relevant facts, metrics, examples, and trends.
Keep the findings factual and concise so the synthesizer can turn them into a polished answer.
""".strip()
    ),
    output_key="research_findings",
)

synthesizer = LlmAgent(
    name="synthesizer",
    model=DEFAULT_MODEL,
    instruction=(
        """
You are the synthesis specialist.

Research plan:
{research_plan}

Research findings:
{research_findings}

Combine the findings into one cohesive, well-structured answer that directly addresses the user's request.
Highlight the most important takeaways first, then support them with the strongest evidence gathered.
If the research findings are incomplete, say so plainly instead of pretending the evidence is stronger than it is.
""".strip()
    ),
)

planner = LlmAgent(
    name="research_planner",
    model=DEFAULT_MODEL,
    instruction="""
You are a research planning specialist.

Break the user's request into exactly three distinct research themes.
Return a practical plan the downstream research pipeline can execute clearly.
Use short headings and concrete investigation steps for each theme.
""".strip(),
    output_key="research_plan",
)

research_agent = SequentialAgent(
    name="research_manager",
    description=load_prompt("research_agent.md"),
    sub_agents=[planner, researcher, synthesizer],
)
