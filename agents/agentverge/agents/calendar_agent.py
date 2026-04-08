from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import AgentTool

from ..config import APP_TZ, DEFAULT_MODEL
from ..prompts import load_prompt
from ..tools.calendar_tools import (
    calendar_toolset,
    format_created_event,
    format_event_details,
    format_events_list,
    resolve_event_ref_to_id,
    set_current_time,
)

planner = LlmAgent(
    name="calendar_planner",
    model=DEFAULT_MODEL,
    instruction="""
You are a calendar intent planner.

Return ONLY valid JSON (no markdown, no extra text).
Choose exactly one intent from:
- LIST_LAST_N_DAYS
- LIST_UPCOMING_N_DAYS
- LIST_RANGE
- GET_EVENT_DETAILS
- CREATE_EVENT

Output schema:
{
  "intent": "LIST_LAST_N_DAYS|LIST_UPCOMING_N_DAYS|LIST_RANGE|GET_EVENT_DETAILS|CREATE_EVENT",
  "days": 7,
  "limit": 10,
  "start_time": null,
  "end_time": null,
  "event_ref": null,
  "create_text": null
}

Rules:
- If user says "last/past/previous ... days/week" => LIST_LAST_N_DAYS. If N missing, days=7.
- If user says "upcoming/next ... days/week" => LIST_UPCOMING_N_DAYS. If N missing, days=7.
- If user provides explicit start & end range => LIST_RANGE.
- If user asks details OR message is just a number like "1" OR "just 1" OR "event 2" => GET_EVENT_DETAILS with event_ref.
- If user asks to create/add/schedule/book a calendar event or meeting => CREATE_EVENT.
- For CREATE_EVENT, put the natural-language event request into create_text.
- limit=10 if not specified.
- days=7 if not specified.
""".strip(),
)

event_creator = LlmAgent(
    name="event_creator",
    model=DEFAULT_MODEL,
    instruction="""
You convert a user's event request into a professional calendar title and a clean quick-add string.

Return ONLY valid JSON (no markdown, no extra text) using this schema:
{
  "title": "string",
  "quick_add_text": "string"
}

Rules:
- Make the title concise, professional, and calendar-friendly.
- Preserve all scheduling details from the user's request.
- Do not invent attendees, location, agenda, or timing details.
- Remove filler phrasing.
- Use title case unless the request clearly calls for another style.
- quick_add_text must start with the polished title, then include the original date/time context.
""".strip(),
)

calendar_manager = LlmAgent(
    name="calendar_manager",
    model=DEFAULT_MODEL,
    description="Handles Google Calendar operations such as listing events, creating meetings, and fetching event details.",
    tools=[
        AgentTool(planner),
        AgentTool(event_creator),
        calendar_toolset,
        format_events_list,
        resolve_event_ref_to_id,
        format_event_details,
        format_created_event,
    ],
    instruction=load_prompt("calendar_agent.md") + f"\n\nTimezone for display: {APP_TZ}\nCurrent time: {{_time}}",
    before_agent_callback=set_current_time,
)
