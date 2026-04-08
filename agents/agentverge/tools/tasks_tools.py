from __future__ import annotations

import asyncio
import re
from datetime import datetime, time, timezone
from typing import Any, Dict, List, Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext

from ..config import APP_TZ, LOCAL_TZ
from ..state.keys import (
    ACTIVE_TASKLIST_ID,
    LAST_TASKLIST_ID_TO_NAME,
    LAST_TASKLIST_INDEX_TO_ID,
    LAST_TASK_INDEX_TO_ID,
    STATE_TIME_KEY,
)
from .google_workspace_toolset import build_google_workspace_toolset


def set_current_time(callback_context: CallbackContext):
    callback_context.state[STATE_TIME_KEY] = datetime.now().astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")


def _now_local() -> datetime:
    return datetime.now().astimezone(LOCAL_TZ)


def _to_rfc3339_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=LOCAL_TZ)
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_text(value: Optional[str], default: str = "-") -> str:
    if not value:
        return default
    cleaned = re.sub(r"\s*\n\s*", " ", value).strip()
    return cleaned or default


def _format_due(value: Optional[str]) -> str:
    if not value:
        return "-"
    try:
        due_dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(LOCAL_TZ)
        return due_dt.strftime("%d %b %Y")
    except ValueError:
        return value


def _format_updated(value: Optional[str]) -> str:
    if not value:
        return "-"
    try:
        updated_dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(LOCAL_TZ)
        return updated_dt.strftime(f"%d %b %Y, %I:%M %p ({APP_TZ})")
    except ValueError:
        return value


def _normalize_status(value: Optional[str]) -> str:
    return "Completed" if value == "completed" else "Needs action"


def _default_task_status_for_create(value: Optional[str]) -> str:
    return "completed" if value == "completed" else "needsAction"


def _normalize_due_rfc3339_for_google_tasks(value: Optional[str]) -> Optional[str]:
    if not value:
        return value

    due_dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if due_dt.tzinfo is None:
        due_dt = due_dt.replace(tzinfo=LOCAL_TZ)

    local_date = due_dt.astimezone(LOCAL_TZ).date()
    normalized = datetime.combine(local_date, time(hour=12), tzinfo=LOCAL_TZ)
    return normalized.isoformat()


tasks_toolset = build_google_workspace_toolset(
    "tasks",
    "v1",
)


def _resolve_google_tasks_tool_names_once() -> Dict[str, str]:
    expected = {
        "tasklists_list": ("_tasks_tasklists_", "_list"),
        "tasks_list": ("_tasks_tasks_", "_list"),
        "tasks_get": ("_tasks_tasks_", "_get"),
        "tasks_insert": ("_tasks_tasks_", "_insert"),
        "tasks_patch": ("_tasks_tasks_", "_patch"),
        "tasks_update": ("_tasks_tasks_", "_update"),
        "tasks_delete": ("_tasks_tasks_", "_delete"),
    }
    fallback = {
        "tasklists_list": "tasks_tasklists_list",
        "tasks_list": "tasks_tasks_list",
        "tasks_get": "tasks_tasks_get",
        "tasks_insert": "tasks_tasks_insert",
        "tasks_patch": "tasks_tasks_patch",
        "tasks_update": "tasks_tasks_update",
        "tasks_delete": "tasks_tasks_delete",
    }

    async def _load_names() -> List[str]:
        tools = await tasks_toolset.get_tools()
        return [tool.name for tool in tools]

    try:
        available_names = asyncio.run(_load_names())
    except Exception:
        return fallback

    resolved: Dict[str, str] = {}
    lowered = {name: name.lower() for name in available_names}
    for key, parts in expected.items():
        match = next(
            (name for name, lowered_name in lowered.items() if all(part in f"_{lowered_name}_" for part in parts)),
            None,
        )
        resolved[key] = match or fallback[key]
    return resolved


RESOLVED_TASK_TOOLS = _resolve_google_tasks_tool_names_once()
TASKLISTS_LIST_TOOL_NAME = RESOLVED_TASK_TOOLS["tasklists_list"]
TASKS_LIST_TOOL_NAME = RESOLVED_TASK_TOOLS["tasks_list"]
TASKS_GET_TOOL_NAME = RESOLVED_TASK_TOOLS["tasks_get"]
TASKS_INSERT_TOOL_NAME = RESOLVED_TASK_TOOLS["tasks_insert"]
TASKS_PATCH_TOOL_NAME = RESOLVED_TASK_TOOLS["tasks_patch"]
TASKS_UPDATE_TOOL_NAME = RESOLVED_TASK_TOOLS["tasks_update"]
TASKS_DELETE_TOOL_NAME = RESOLVED_TASK_TOOLS["tasks_delete"]
TASKS_WRITE_TOOL_NAME = TASKS_PATCH_TOOL_NAME or TASKS_UPDATE_TOOL_NAME


def format_tasklists(tasklists: List[Dict[str, Any]], tool_context: ToolContext) -> str:
    if not tasklists:
        tool_context.state[LAST_TASKLIST_INDEX_TO_ID] = {}
        tool_context.state[LAST_TASKLIST_ID_TO_NAME] = {}
        return "No task lists found."

    index_map: Dict[str, str] = {}
    name_map: Dict[str, str] = {}
    active_id = tool_context.state.get(ACTIVE_TASKLIST_ID)
    lines = ["Here are your task lists:\n"]
    for index, tasklist in enumerate(tasklists, start=1):
        tasklist_id = tasklist.get("id", "")
        title = tasklist.get("title") or "(Untitled list)"
        index_map[str(index)] = tasklist_id
        name_map[tasklist_id] = title
        marker = " (active)" if active_id and active_id == tasklist_id else ""
        lines.append(f"{index}. {title}{marker}\n   Tasklist ID: {tasklist_id}\n")

    tool_context.state[LAST_TASKLIST_INDEX_TO_ID] = index_map
    tool_context.state[LAST_TASKLIST_ID_TO_NAME] = name_map

    if not active_id and tasklists:
        first = tasklists[0]
        tool_context.state[ACTIVE_TASKLIST_ID] = first.get("id")
        lines.append(f"Active task list is now {first.get('title') or '(Untitled list)'} ({first.get('id', '-')}).")

    lines.append("Tip: You can say 'use list 2' or provide a tasklist ID.")
    return "\n".join(lines)


def resolve_tasklist_ref_to_id(tasklist_ref: str, tool_context: ToolContext) -> str:
    text = (tasklist_ref or "").strip()
    if not text:
        return tool_context.state.get(ACTIVE_TASKLIST_ID, "")

    lowered = text.lower()
    if lowered in {"active", "current", "active list", "current list"}:
        return tool_context.state.get(ACTIVE_TASKLIST_ID, "")

    match = re.search(r"\b(\d+)\b", lowered)
    if match:
        resolved = (tool_context.state.get(LAST_TASKLIST_INDEX_TO_ID, {}) or {}).get(match.group(1))
        if resolved:
            return resolved

    return text


def set_active_tasklist(tasklist_id: str, tasklist_name: Optional[str], tool_context: ToolContext) -> str:
    tool_context.state[ACTIVE_TASKLIST_ID] = tasklist_id
    if tasklist_name:
        id_to_name = tool_context.state.get(LAST_TASKLIST_ID_TO_NAME, {}) or {}
        id_to_name[tasklist_id] = tasklist_name
        tool_context.state[LAST_TASKLIST_ID_TO_NAME] = id_to_name
    display_name = tasklist_name or (tool_context.state.get(LAST_TASKLIST_ID_TO_NAME, {}) or {}).get(tasklist_id) or "-"
    return f"Active task list set to {display_name} ({tasklist_id})."


def ensure_active_tasklist(tasklists: List[Dict[str, Any]], tool_context: ToolContext) -> str:
    active_id = tool_context.state.get(ACTIVE_TASKLIST_ID)
    if active_id:
        return active_id
    if not tasklists:
        return ""

    first = tasklists[0]
    tasklist_id = first.get("id", "")
    tasklist_name = first.get("title") or "(Untitled list)"
    tool_context.state[ACTIVE_TASKLIST_ID] = tasklist_id

    id_to_name = tool_context.state.get(LAST_TASKLIST_ID_TO_NAME, {}) or {}
    id_to_name[tasklist_id] = tasklist_name
    tool_context.state[LAST_TASKLIST_ID_TO_NAME] = id_to_name
    return tasklist_id


def get_active_tasklist_header(tool_context: ToolContext) -> str:
    tasklist_id = tool_context.state.get(ACTIVE_TASKLIST_ID) or "-"
    tasklist_name = (tool_context.state.get(LAST_TASKLIST_ID_TO_NAME, {}) or {}).get(tasklist_id, "-")
    return f"Active task list: {tasklist_name} ({tasklist_id})"


def format_tasks_list(tasks: List[Dict[str, Any]], tool_context: ToolContext) -> str:
    header = get_active_tasklist_header(tool_context)
    if not tasks:
        tool_context.state[LAST_TASK_INDEX_TO_ID] = {}
        return header + "\n\nNo tasks found in this list."

    index_map: Dict[str, str] = {}
    lines = [header, "", "Here are the tasks:\n"]
    for index, task in enumerate(tasks, start=1):
        task_id = task.get("id", "")
        index_map[str(index)] = task_id
        lines.append(
            f"{index}. {task.get('title') or '(Untitled task)'}\n"
            f"   Due: {_format_due(task.get('due'))}\n"
            f"   Status: {_normalize_status(task.get('status'))}\n"
            f"   Task ID: {task_id}\n"
        )
    tool_context.state[LAST_TASK_INDEX_TO_ID] = index_map
    return "\n".join(lines)


def resolve_task_ref_to_id(task_ref: str, tool_context: ToolContext) -> str:
    match = re.search(r"\b(\d+)\b", (task_ref or "").strip().lower())
    if match:
        resolved = (tool_context.state.get(LAST_TASK_INDEX_TO_ID, {}) or {}).get(match.group(1))
        if resolved:
            return resolved
    return (task_ref or "").strip()


def format_task_details(task: Dict[str, Any], tool_context: ToolContext) -> str:
    detail_rows = [
        ("Title", task.get("title") or "(Untitled task)"),
        ("Notes", _normalize_text(task.get("notes"))),
        ("Due", _format_due(task.get("due"))),
        ("Status", _normalize_status(task.get("status"))),
        ("Updated", _format_updated(task.get("updated"))),
        ("Task ID", task.get("id") or "-"),
        ("Tasklist ID", tool_context.state.get(ACTIVE_TASKLIST_ID) or "-"),
    ]

    lines = ["## Task Details", "", "| Field | Value |", "| --- | --- |"]
    for label, value in detail_rows:
        safe_value = str(value).replace("|", "\\|")
        lines.append(f"| {label} | {safe_value} |")
    return "\n".join(lines) + "\n"


def build_task_payload(
    task_fields: Dict[str, Any],
    existing_task: Optional[Dict[str, Any]] = None,
    mark_complete: bool = False,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}

    if existing_task is None:
        title = (task_fields.get("title") or "").strip()
        if not title:
            raise ValueError("Task title is required.")
        payload["title"] = title
        if task_fields.get("notes") is not None:
            payload["notes"] = task_fields.get("notes")
        if task_fields.get("due_rfc3339") is not None:
            payload["due"] = _normalize_due_rfc3339_for_google_tasks(task_fields.get("due_rfc3339"))
        payload["status"] = _default_task_status_for_create(task_fields.get("status"))
        if payload["status"] == "completed":
            payload["completed"] = _to_rfc3339_z(_now_local())
        return payload

    if task_fields.get("title") is not None:
        payload["title"] = task_fields.get("title")
    if task_fields.get("notes") is not None:
        payload["notes"] = task_fields.get("notes")
    if task_fields.get("due_rfc3339") is not None:
        payload["due"] = _normalize_due_rfc3339_for_google_tasks(task_fields.get("due_rfc3339"))
    if task_fields.get("status") is not None:
        payload["status"] = task_fields.get("status")

    if mark_complete:
        payload["status"] = "completed"
        payload["completed"] = _to_rfc3339_z(_now_local())
    elif payload.get("status") == "completed":
        payload["completed"] = _to_rfc3339_z(_now_local())

    return payload


def format_task_write_result(action: str, task: Dict[str, Any], tool_context: ToolContext) -> str:
    if action == "delete":
        return (
            f"Task deleted successfully.\n\nTask ID: {task.get('id', '-')}\n"
            f"Tasklist ID: {tool_context.state.get(ACTIVE_TASKLIST_ID, '-')}"
        )

    action_line = {
        "create": "Task created successfully.",
        "update": "Task updated successfully.",
        "complete": "Task marked complete successfully.",
    }.get(action, "Task updated successfully.")
    return action_line + "\n\n" + format_task_details(task, tool_context)
