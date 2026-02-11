# ABOUTME: Processes incoming signals from email, calendar, and manual input.
# ABOUTME: Uses Claude to extract actionable tasks from unstructured content.

import json
from datetime import datetime
from typing import List, Optional

from seren_llm import get_seren_claude_client

from config import get_model_for_task
from models import Priority, SignalSource, Task


def process_signal(source: str, payload: dict, user_id: str) -> List[Task]:
    """Extract tasks from signal using AI.

    Args:
        source: Signal source (email, calendar, manual)
        payload: Signal payload with content
        user_id: User ID for task assignment

    Returns:
        List of extracted tasks
    """
    if source == "email":
        return extract_from_email(payload, user_id)
    elif source == "calendar":
        return extract_from_calendar(payload, user_id)
    elif source == "manual":
        return [create_manual_task(payload, user_id)]
    else:
        return []


def extract_from_email(email: dict, user_id: str) -> List[Task]:
    """Use Claude to extract tasks from email content.

    Args:
        email: Email data with from, subject, body fields
        user_id: User ID for task assignment

    Returns:
        List of extracted tasks
    """
    client = get_seren_claude_client()
    model = get_model_for_task("task_extraction")

    prompt = f"""Analyze this email and extract actionable tasks.

From: {email.get('from', 'Unknown')}
Subject: {email.get('subject', 'No subject')}
Body: {email.get('body', '')}

For each task, provide:
- title: action verb + object (e.g., "Send pricing doc to John")
- priority: low, medium, high, or urgent
- due_date: ISO date if mentioned, null otherwise
- tags: relevant labels as array

Return a JSON array of tasks. Return empty array [] if no action needed.

Example output:
[
  {{"title": "Send pricing doc", "priority": "medium", "due_date": "2026-01-25", "tags": ["sales"]}},
  {{"title": "Schedule follow-up call", "priority": "low", "due_date": null, "tags": ["meeting"]}}
]

Output only valid JSON, no explanation."""

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        response_text = response.content[0].text.strip()
        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        tasks_data = json.loads(response_text)

        tasks = []
        for t in tasks_data:
            task = Task(
                title=t["title"],
                priority=Priority(t.get("priority", "medium")),
                due_date=datetime.fromisoformat(t["due_date"]) if t.get("due_date") else None,
                tags=t.get("tags", []),
                source=SignalSource.EMAIL,
                user_id=user_id,
            )
            tasks.append(task)
        return tasks
    except (json.JSONDecodeError, KeyError, ValueError):
        return []


def extract_from_calendar(event: dict, user_id: str) -> List[Task]:
    """Extract prep tasks from calendar events.

    Args:
        event: Calendar event data
        user_id: User ID for task assignment

    Returns:
        List of prep tasks for the event
    """
    client = get_seren_claude_client()
    model = get_model_for_task("calendar_prep")

    event_time = event.get("start_time", "")
    event_title = event.get("title", "Untitled event")
    attendees = event.get("attendees", [])

    prompt = f"""Analyze this calendar event and suggest preparation tasks.

Event: {event_title}
Time: {event_time}
Attendees: {', '.join(attendees) if attendees else 'None listed'}
Description: {event.get('description', 'No description')}

Suggest prep tasks that should be done BEFORE this meeting.
Consider:
- Materials to prepare
- Research about attendees or topics
- Documents to review or create
- Questions to prepare

For each task, provide:
- title: preparation action (e.g., "Prepare demo slides for product review")
- priority: low, medium, or high
- tags: relevant labels

Return a JSON array. Return empty array [] if no prep needed.
Output only valid JSON, no explanation."""

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        response_text = response.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        tasks_data = json.loads(response_text)

        tasks = []
        for t in tasks_data:
            # Set due date to before the event
            due_date = None
            if event_time:
                try:
                    event_dt = datetime.fromisoformat(event_time.replace("Z", "+00:00"))
                    # Due 1 hour before event
                    from datetime import timedelta

                    due_date = event_dt - timedelta(hours=1)
                except (ValueError, TypeError):
                    pass

            task = Task(
                title=t["title"],
                priority=Priority(t.get("priority", "medium")),
                due_date=due_date,
                tags=t.get("tags", []) + ["meeting-prep"],
                source=SignalSource.CALENDAR,
                user_id=user_id,
            )
            tasks.append(task)
        return tasks
    except (json.JSONDecodeError, KeyError, ValueError):
        return []


def create_manual_task(payload: dict, user_id: str) -> Task:
    """Create a task from manual input.

    Args:
        payload: Task data from user input
        user_id: User ID for task assignment

    Returns:
        Created task
    """
    due_date = None
    if payload.get("due_date"):
        try:
            due_date = datetime.fromisoformat(payload["due_date"])
        except ValueError:
            pass

    return Task(
        title=payload.get("title", "Untitled task"),
        description=payload.get("description"),
        priority=Priority(payload.get("priority", "medium")),
        due_date=due_date,
        tags=payload.get("tags", []),
        source=SignalSource.MANUAL,
        user_id=user_id,
    )


def check_duplicate(new_task: Task, existing_tasks: List[Task]) -> Optional[Task]:
    """Check if a similar task already exists using AI.

    Args:
        new_task: Task to check
        existing_tasks: List of existing tasks to compare against

    Returns:
        Matching task if found, None otherwise
    """
    if not existing_tasks:
        return None

    client = get_seren_claude_client()
    model = get_model_for_task("deduplication")

    existing_titles = [t.title for t in existing_tasks]

    prompt = f"""Check if this new task is a duplicate of any existing task.

New task: "{new_task.title}"

Existing tasks:
{json.dumps(existing_titles, indent=2)}

If the new task is semantically similar to an existing task (same action/intent),
return the index (0-based) of the matching task.
If no match, return -1.

Output only the number, nothing else."""

    response = client.messages.create(
        model=model,
        max_tokens=10,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        index = int(response.content[0].text.strip())
        if 0 <= index < len(existing_tasks):
            return existing_tasks[index]
    except (ValueError, IndexError):
        pass

    return None


def classify_signal(source: str, payload: dict) -> dict:
    """Classify whether a signal is actionable or informational.

    Args:
        source: Signal source
        payload: Signal payload

    Returns:
        Classification with actionable flag and priority
    """
    client = get_seren_claude_client()
    model = get_model_for_task("task_extraction")

    content = ""
    if source == "email":
        content = f"Subject: {payload.get('subject', '')}\nBody: {payload.get('body', '')}"
    elif source == "calendar":
        content = f"Event: {payload.get('title', '')}\nDescription: {payload.get('description', '')}"

    prompt = f"""Classify this {source} content:

{content}

Determine:
1. Is this actionable (requires a task to be created)?
2. What priority level? (low, medium, high, urgent)

Return JSON:
{{"actionable": true/false, "priority": "low/medium/high/urgent", "reason": "brief explanation"}}

Output only valid JSON."""

    response = client.messages.create(
        model=model,
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        response_text = response.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()
        return json.loads(response_text)
    except (json.JSONDecodeError, ValueError):
        return {"actionable": False, "priority": "low", "reason": "Could not classify"}
