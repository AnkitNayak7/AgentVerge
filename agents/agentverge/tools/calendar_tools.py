from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext

from ..config import APP_TZ, LOCAL_TZ, OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET
from ..state.keys import LAST_EVENT_INDEX_TO_ID, STATE_TIME_KEY
from .google_workspace_toolset import build_google_workspace_toolset


def set_current_time(callback_context: CallbackContext):
    callback_context.state[STATE_TIME_KEY] = datetime.now().astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")


def _format_duration(start_dt: datetime, end_dt: datetime) -> str:
    total_minutes = int((end_dt - start_dt).total_seconds() // 60)
    if total_minutes < 0:
        return "-"
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def _normalize_text(value: Optional[str], default: str = "-") -> str:
    if not value:
        return default
    cleaned = re.sub(r"\s*\n\s*", " ", value).strip()
    return cleaned or default


calendar_toolset = build_google_workspace_toolset(
    "calendar",
    "v3",
    tool_filter=[
        "calendar_events_list",
        "calendar_events_get",
        "calendar_events_quick_add",
    ],
    tool_name_prefix="google",
)


def format_events_list(events: List[Dict[str, Any]], tool_context: ToolContext) -> str:
    if not events:
        tool_context.state[LAST_EVENT_INDEX_TO_ID] = {}
        tool_context.state["last_list_count"] = 0
        return "No events found for this period."

    index_map: Dict[str, str] = {}
    lines: List[str] = ["Here are your calendar events:\n"]

    for index, event in enumerate(events, start=1):
        event_id = event.get("id", "")
        index_map[str(index)] = event_id
        title = event.get("summary") or "(No title)"
        agenda = _normalize_text(event.get("description"))
        if len(agenda) > 180:
            agenda = agenda[:177] + "..."

        start_raw = (event.get("start") or {}).get("dateTime") or (event.get("start") or {}).get("date")
        end_raw = (event.get("end") or {}).get("dateTime") or (event.get("end") or {}).get("date")
        is_all_day = start_raw and len(start_raw) == 10 and end_raw and len(end_raw) == 10

        if is_all_day:
            start_dt = datetime.fromisoformat(start_raw).replace(tzinfo=LOCAL_TZ)
            end_dt = datetime.fromisoformat(end_raw).replace(tzinfo=LOCAL_TZ)
            days = max((end_dt.date() - start_dt.date()).days, 1)
            time_str = f"{start_dt.strftime('%d %b %Y')} (All-day)"
            duration_str = f"{days} day(s)"
        else:
            start_dt = datetime.fromisoformat(start_raw.replace("Z", "+00:00")).astimezone(LOCAL_TZ)
            end_dt = datetime.fromisoformat(end_raw.replace("Z", "+00:00")).astimezone(LOCAL_TZ)
            time_str = f"{start_dt.strftime('%d %b %Y, %I:%M %p')} - {end_dt.strftime('%I:%M %p')} ({APP_TZ})"
            duration_str = _format_duration(start_dt, end_dt)

        lines.append(
            f"{index}. {title}\n"
            f"   Time: {time_str}\n"
            f"   Duration: {duration_str}\n"
            f"   Agenda: {agenda}\n"
            f"   Event ID: {event_id}\n"
        )

    tool_context.state[LAST_EVENT_INDEX_TO_ID] = index_map
    tool_context.state["last_list_count"] = len(events)
    lines.append("Tip: You can say 'details of 1', 'just 1', or 'show event 2 details'.")
    return "\n".join(lines)


def resolve_event_ref_to_id(event_ref: str, tool_context: ToolContext) -> str:
    match = re.search(r"\b(\d+)\b", event_ref.strip().lower())
    if match:
        resolved = (tool_context.state.get(LAST_EVENT_INDEX_TO_ID, {}) or {}).get(match.group(1))
        if resolved:
            return resolved
    return event_ref.strip()


def format_event_details(event: Dict[str, Any]) -> str:
    title = event.get("summary") or "(No title)"
    agenda = _normalize_text(event.get("description"))
    if len(agenda) > 500:
        agenda = agenda[:497] + "..."

    start_raw = (event.get("start") or {}).get("dateTime") or (event.get("start") or {}).get("date")
    end_raw = (event.get("end") or {}).get("dateTime") or (event.get("end") or {}).get("date")
    is_all_day = start_raw and len(start_raw) == 10 and end_raw and len(end_raw) == 10

    if is_all_day:
        start_dt = datetime.fromisoformat(start_raw).replace(tzinfo=LOCAL_TZ)
        end_dt = datetime.fromisoformat(end_raw).replace(tzinfo=LOCAL_TZ)
        days = max((end_dt.date() - start_dt.date()).days, 1)
        time_str = f"{start_dt.strftime('%d %b %Y')} (All-day)"
        duration_str = f"{days} day(s)"
    else:
        start_dt = datetime.fromisoformat(start_raw.replace("Z", "+00:00")).astimezone(LOCAL_TZ)
        end_dt = datetime.fromisoformat(end_raw.replace("Z", "+00:00")).astimezone(LOCAL_TZ)
        time_str = f"{start_dt.strftime('%d %b %Y, %I:%M %p')} - {end_dt.strftime('%I:%M %p')} ({APP_TZ})"
        duration_str = _format_duration(start_dt, end_dt)

    rows = [
        ("Title", title),
        ("Time", time_str),
        ("Duration", duration_str),
        ("Location", _normalize_text(event.get("location"))),
        ("Agenda", agenda),
        ("Meet Link", event.get("hangoutLink") or "-"),
        ("Event Link", event.get("htmlLink") or "-"),
        ("Event ID", event.get("id", "") or "-"),
    ]

    lines = ["## Event Details", "", "| Field | Value |", "| --- | --- |"]
    for label, value in rows:
        safe_value = str(value).replace("|", "\\|")
        lines.append(f"| {label} | {safe_value} |")
    return "\n".join(lines) + "\n"


def format_created_event(event: Dict[str, Any]) -> str:
    return "Event created successfully.\n\n" + format_event_details(event)
