from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import AgentTool

from ..config import APP_TZ, DEFAULT_MODEL
from ..prompts import load_prompt
from ..tools.tasks_tools import (
    TASKLISTS_LIST_TOOL_NAME,
    TASKS_DELETE_TOOL_NAME,
    TASKS_GET_TOOL_NAME,
    TASKS_INSERT_TOOL_NAME,
    TASKS_LIST_TOOL_NAME,
    TASKS_PATCH_TOOL_NAME,
    TASKS_UPDATE_TOOL_NAME,
    build_task_payload,
    ensure_active_tasklist,
    format_task_details,
    format_task_write_result,
    format_tasklists,
    format_tasks_list,
    get_active_tasklist_header,
    resolve_task_ref_to_id,
    resolve_tasklist_ref_to_id,
    set_active_tasklist,
    set_current_time,
    tasks_toolset,
)

tasks_planner = LlmAgent(
    name="tasks_planner",
    model=DEFAULT_MODEL,
    instruction="""
You are a Google Tasks intent planner.

Return ONLY valid JSON (no markdown, no extra text).
Choose exactly one intent from:
- LIST_TASKLISTS
- SET_ACTIVE_LIST
- LIST_TASKS
- GET_TASK_DETAILS
- CREATE_TASK
- UPDATE_TASK
- COMPLETE_TASK
- DELETE_TASK

Output schema:
{
  "intent": "LIST_TASKLISTS|SET_ACTIVE_LIST|LIST_TASKS|GET_TASK_DETAILS|CREATE_TASK|UPDATE_TASK|COMPLETE_TASK|DELETE_TASK",
  "tasklist_ref": null,
  "task_ref": null,
  "task_request": null,
  "limit": 20
}

Rules:
- Choose LIST_TASKLISTS only when the user explicitly asks about task lists.
- If the user asks to switch/use/select/set a specific list => SET_ACTIVE_LIST.
- If the user asks to show/list tasks => LIST_TASKS.
- If the user asks for task details or says only a task number like "1" or "task 2" => GET_TASK_DETAILS.
- If the user asks to create/add a task => CREATE_TASK and copy the user's full task request into task_request.
- If the user asks to edit/update/change/rename a task => UPDATE_TASK and copy the user's full task request into task_request.
- If the user asks to mark a task done/complete/finished => COMPLETE_TASK.
- If the user asks to delete/remove a task => DELETE_TASK.
- If the user clearly refers to a task or to-do, do not classify it as a calendar request.
- Preserve date phrases like "today", "tomorrow", and "next Monday" inside task_request.
""".strip(),
)

task_writer = LlmAgent(
    name="task_writer",
    model=DEFAULT_MODEL,
    instruction="""
You convert a user's Google Tasks request into structured task fields.

Return ONLY valid JSON (no markdown, no extra text) using this schema:
{
  "title": "string|null",
  "notes": "string|null",
  "due_rfc3339": "string|null",
  "status": "needsAction|completed|null"
}

Rules:
- Resolve relative dates using the provided current local time.
- For CREATE requests, infer the task title and explicit notes/due date/status.
- For UPDATE requests, treat fields as partial edits.
- Only include a field when the user explicitly asked to set or change it.
- Never invent notes, title, due dates, or status.
- If the user specifies a date without a time, return due_rfc3339 in RFC3339 using local noon for that date.
- If the user says "today", resolve it against the provided current local time, not against any assumed default date.
- due_rfc3339 must be RFC3339 if provided.
""".strip(),
)

tasks_manager = LlmAgent(
    name="tasks_manager",
    model=DEFAULT_MODEL,
    description="Handles Google Tasks operations such as creating, listing, updating, completing, and deleting tasks.",
    tools=[
        AgentTool(tasks_planner),
        AgentTool(task_writer),
        tasks_toolset,
        format_tasklists,
        resolve_tasklist_ref_to_id,
        set_active_tasklist,
        ensure_active_tasklist,
        get_active_tasklist_header,
        format_tasks_list,
        resolve_task_ref_to_id,
        format_task_details,
        build_task_payload,
        format_task_write_result,
    ],
    instruction=(
        load_prompt("tasks_agent.md")
        + "\n\n"
        + f"Available Google Tasks tools:\n"
        + f"- List task lists: {TASKLISTS_LIST_TOOL_NAME}\n"
        + f"- List tasks: {TASKS_LIST_TOOL_NAME}\n"
        + f"- Get task details: {TASKS_GET_TOOL_NAME}\n"
        + f"- Create task: {TASKS_INSERT_TOOL_NAME}\n"
        + f"- Update task: prefer {TASKS_PATCH_TOOL_NAME}, fallback {TASKS_UPDATE_TOOL_NAME}\n"
        + f"- Delete task: {TASKS_DELETE_TOOL_NAME}\n\n"
        + f"Timezone for display: {APP_TZ}\nCurrent time: {{_time}}"
    ),
    before_agent_callback=set_current_time,
)
