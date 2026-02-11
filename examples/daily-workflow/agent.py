# ABOUTME: Main entry point for the Daily Workflow Agent.
# ABOUTME: Handles task management with configurable autonomy levels.

"""
Daily Workflow Agent

Manages daily tasks with AI-powered task extraction from email and calendar,
configurable autonomy levels, and intelligent prioritization.

Price: $0.005 per invocation
"""

from datetime import datetime, timedelta
from typing import List

from seren_agent import agent
from seren_agent.llm import get_anthropic_client

from actions import (
    create_task,
    execute_action,
    get_pending_reminders,
    get_tasks,
)
from config import AutonomyConfig, UserPreferences, get_model_for_task
from models import Priority, Task, TaskStatus
from signals import check_duplicate, classify_signal, process_signal


@agent(
    name="Daily Workflow Agent",
    description="Manages daily tasks with reminders and follow-ups. "
    "Extracts tasks from email and calendar, prioritizes intelligently, "
    "and respects your autonomy preferences.",
    price="0.005",
)
def run(input: dict) -> dict:
    """
    Process workflow signals and manage tasks.

    Input types:
    - {"type": "signal", "source": "email|calendar|manual", "payload": {...}, "user_id": "..."}
    - {"type": "digest", "user_id": "..."}
    - {"type": "action", "action_type": "...", "payload": {...}, "user_id": "..."}
    - {"type": "query", "query_type": "tasks|reminders", "filters": {...}, "user_id": "..."}
    - {"type": "check_reminders", "user_id": "..."}
    - {"type": "scan_overdue", "user_id": "..."}

    Returns:
        dict with result data and any tasks/reminders affected
    """
    input_type = input.get("type")
    user_id = input.get("user_id", "")

    if not user_id:
        return {"error": "Missing required field: user_id"}

    # Load user preferences (in production, this would come from storage)
    preferences = get_user_preferences(user_id)

    if input_type == "signal":
        return handle_signal(input, preferences)
    elif input_type == "digest":
        return generate_digest(user_id, preferences)
    elif input_type == "action":
        return handle_action(input, preferences)
    elif input_type == "query":
        return handle_query(input)
    elif input_type == "check_reminders":
        return check_reminders(user_id, preferences)
    elif input_type == "scan_overdue":
        return scan_overdue(user_id, preferences)
    else:
        return {"error": f"Unknown input type: {input_type}"}


def get_user_preferences(user_id: str) -> UserPreferences:
    """Load user preferences from storage.

    In production, this would fetch from SerenDB.
    For now, returns default preferences.
    """
    return UserPreferences(user_id=user_id)


def handle_signal(input: dict, preferences: UserPreferences) -> dict:
    """Process an incoming signal and extract tasks.

    Args:
        input: Signal input with source and payload
        preferences: User preferences

    Returns:
        dict with extracted tasks and actions taken
    """
    source = input.get("source", "")
    payload = input.get("payload", {})
    user_id = input.get("user_id", "")

    if not source or not payload:
        return {"error": "Missing source or payload"}

    # Classify the signal first
    classification = classify_signal(source, payload)

    if not classification.get("actionable", False):
        return {
            "status": "informational",
            "classification": classification,
            "tasks_created": 0,
        }

    # Extract tasks from the signal
    tasks = process_signal(source, payload, user_id)

    if not tasks:
        return {
            "status": "no_tasks",
            "classification": classification,
            "tasks_created": 0,
        }

    # Check for duplicates
    existing_tasks = get_tasks(user_id, status=TaskStatus.PENDING)
    created_tasks = []
    duplicates = []

    for task in tasks:
        duplicate = check_duplicate(task, existing_tasks)
        if duplicate:
            duplicates.append({"new": task.title, "existing": duplicate.title})
        else:
            # Create the task respecting autonomy
            result = execute_action(
                "create_task",
                task.to_dict(),
                preferences.autonomy,
                user_id,
            )
            if result.status in ("created", "pending_approval"):
                created_tasks.append(task.to_dict())
                existing_tasks.append(task)  # Prevent duplicate in same batch

    return {
        "status": "processed",
        "classification": classification,
        "tasks_created": len(created_tasks),
        "tasks": created_tasks,
        "duplicates_skipped": len(duplicates),
        "duplicate_details": duplicates,
    }


def generate_digest(user_id: str, preferences: UserPreferences) -> dict:
    """Generate morning digest of tasks.

    Args:
        user_id: User ID
        preferences: User preferences

    Returns:
        dict with formatted digest
    """
    now = datetime.utcnow()
    today_end = now.replace(hour=23, minute=59, second=59)
    week_end = now + timedelta(days=7)

    # Get tasks by category
    all_tasks = get_tasks(user_id)
    pending_tasks = [t for t in all_tasks if t.status == TaskStatus.PENDING]

    overdue = []
    due_today = []
    upcoming = []
    completed_yesterday = []

    yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0)

    for task in all_tasks:
        if task.status == TaskStatus.COMPLETED:
            if task.completed_at and task.completed_at >= yesterday_start:
                completed_yesterday.append(task)
        elif task.due_date:
            if task.due_date < now:
                overdue.append(task)
            elif task.due_date <= today_end:
                due_today.append(task)
            elif task.due_date <= week_end:
                upcoming.append(task)

    # Sort by priority
    overdue.sort(key=lambda t: (t.priority != Priority.URGENT, t.due_date or now))
    due_today.sort(key=lambda t: (t.priority != Priority.URGENT, t.due_date or now))
    upcoming.sort(key=lambda t: t.due_date or week_end)

    # Format digest
    client = get_anthropic_client()
    model = get_model_for_task("reminder_formatting")

    digest_data = {
        "date": now.strftime("%A, %B %d"),
        "overdue": [t.to_dict() for t in overdue[:5]],
        "due_today": [t.to_dict() for t in due_today[:10]],
        "upcoming": [t.to_dict() for t in upcoming[:5]],
        "completed_yesterday": [t.to_dict() for t in completed_yesterday[:5]],
    }

    # Use AI to format a friendly digest
    prompt = f"""Format this task data into a friendly daily digest.
Use emoji sparingly. Keep it scannable.

Data:
{digest_data}

Format like:
📋 Your Day — [date]

OVERDUE (action needed)
• task (X days late)

DUE TODAY
• task 1
• task 2

UPCOMING THIS WEEK
• task (Day)

COMPLETED YESTERDAY
✓ task

Keep it brief and actionable."""

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    digest_text = response.content[0].text

    return {
        "status": "generated",
        "digest": digest_text,
        "summary": {
            "overdue_count": len(overdue),
            "due_today_count": len(due_today),
            "upcoming_count": len(upcoming),
            "completed_yesterday_count": len(completed_yesterday),
        },
    }


def handle_action(input: dict, preferences: UserPreferences) -> dict:
    """Handle an action request.

    Args:
        input: Action input with action_type and payload
        preferences: User preferences

    Returns:
        dict with action result
    """
    action_type = input.get("action_type", "")
    payload = input.get("payload", {})
    user_id = input.get("user_id", "")

    if not action_type:
        return {"error": "Missing action_type"}

    result = execute_action(action_type, payload, preferences.autonomy, user_id)

    return {
        "status": result.status,
        "result": result.result,
        "reason": result.reason,
        "proposal": result.proposal,
    }


def handle_query(input: dict) -> dict:
    """Handle a query request.

    Args:
        input: Query input with query_type and filters

    Returns:
        dict with query results
    """
    query_type = input.get("query_type", "")
    filters = input.get("filters", {})
    user_id = input.get("user_id", "")

    if query_type == "tasks":
        status_filter = None
        if filters.get("status"):
            status_filter = TaskStatus(filters["status"])

        due_before = None
        if filters.get("due_before"):
            due_before = datetime.fromisoformat(filters["due_before"])

        tasks = get_tasks(user_id, status=status_filter, due_before=due_before)
        return {
            "status": "success",
            "tasks": [t.to_dict() for t in tasks],
            "count": len(tasks),
        }

    elif query_type == "reminders":
        until = datetime.utcnow() + timedelta(hours=24)
        if filters.get("until"):
            until = datetime.fromisoformat(filters["until"])

        reminders = get_pending_reminders(user_id, until)
        return {
            "status": "success",
            "reminders": [r.to_dict() for r in reminders],
            "count": len(reminders),
        }

    else:
        return {"error": f"Unknown query_type: {query_type}"}


def check_reminders(user_id: str, preferences: UserPreferences) -> dict:
    """Check for due reminders and send notifications.

    Args:
        user_id: User ID
        preferences: User preferences

    Returns:
        dict with reminders sent
    """
    now = datetime.utcnow()
    reminders = get_pending_reminders(user_id, now)

    sent = []
    for reminder in reminders:
        # In production, this would send actual notifications
        # For now, just mark as processed
        sent.append(reminder.to_dict())

    return {
        "status": "checked",
        "reminders_due": len(reminders),
        "reminders_sent": len(sent),
        "reminders": sent,
    }


def scan_overdue(user_id: str, preferences: UserPreferences) -> dict:
    """Scan for overdue tasks and flag them.

    Args:
        user_id: User ID
        preferences: User preferences

    Returns:
        dict with overdue tasks found
    """
    now = datetime.utcnow()
    tasks = get_tasks(user_id, status=TaskStatus.PENDING)

    overdue = []
    for task in tasks:
        if task.due_date and task.due_date < now:
            days_overdue = (now - task.due_date).days
            overdue.append({
                "task": task.to_dict(),
                "days_overdue": days_overdue,
            })

    # Sort by most overdue first
    overdue.sort(key=lambda x: -x["days_overdue"])

    return {
        "status": "scanned",
        "overdue_count": len(overdue),
        "overdue_tasks": overdue[:10],  # Top 10 most overdue
    }


if __name__ == "__main__":
    # Local testing
    from seren_agent.testing import test_agent

    # Test signal processing
    result = test_agent(
        run,
        {
            "type": "signal",
            "source": "email",
            "user_id": "test-user",
            "payload": {
                "from": "john@example.com",
                "subject": "Meeting follow-up",
                "body": "Thanks for the demo! Can you send the pricing doc by Friday?",
            },
        },
        env={"ANTHROPIC_API_KEY": "your-key-here"},
    )
    print("Signal result:", result)

    # Test digest generation
    result = test_agent(
        run,
        {"type": "digest", "user_id": "test-user"},
        env={"ANTHROPIC_API_KEY": "your-key-here"},
    )
    print("Digest result:", result)
