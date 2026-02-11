# ABOUTME: Executes workflow actions like creating tasks and sending reminders.
# ABOUTME: Respects autonomy levels for each action type and logs all executions.

import os
from datetime import datetime
from typing import List, Optional

import httpx

from config import AutonomyConfig
from models import (
    ActionResult,
    AutonomyLevel,
    ExecutionLog,
    Priority,
    Reminder,
    Task,
    TaskStatus,
)


# Seren API configuration
SEREN_API_URL = os.environ.get("SEREN_API_URL", "https://api.serendb.com")
SEREN_API_KEY = os.environ.get("SEREN_API_KEY", "")


def execute_action(
    action_type: str,
    payload: dict,
    autonomy_config: AutonomyConfig,
    user_id: str,
) -> ActionResult:
    """Execute action based on type and autonomy level.

    Args:
        action_type: Type of action to execute
        payload: Action payload
        autonomy_config: User's autonomy configuration
        user_id: User ID for logging

    Returns:
        ActionResult with status and details
    """
    autonomy_level = autonomy_config.get_level(action_type)

    # Manual means agent doesn't act
    if autonomy_level == AutonomyLevel.MANUAL:
        return ActionResult(status="skipped", reason="manual_mode")

    # Suggest means propose and wait for approval
    if autonomy_level == AutonomyLevel.SUGGEST:
        return ActionResult(status="pending_approval", proposal=payload)

    # Route to appropriate handler
    handlers = {
        "create_task": create_task,
        "complete_task": complete_task,
        "reschedule_task": reschedule_task,
        "update_task": update_task,
        "delete_task": delete_task,
        "create_reminder": create_reminder,
        "log_context": log_context,
    }

    handler = handlers.get(action_type)
    if not handler:
        return ActionResult(status="error", reason=f"Unknown action: {action_type}")

    result = handler(payload, user_id)

    # Log execution for audit trail
    log_execution(user_id, action_type, payload, result, autonomy_level)

    return result


def create_task(payload: dict, user_id: str) -> ActionResult:
    """Create a new task in SerenDB.

    Args:
        payload: Task data
        user_id: User ID

    Returns:
        ActionResult with created task
    """
    task = Task(
        title=payload.get("title", "Untitled"),
        description=payload.get("description"),
        priority=Priority(payload.get("priority", "medium")),
        due_date=(
            datetime.fromisoformat(payload["due_date"])
            if payload.get("due_date")
            else None
        ),
        tags=payload.get("tags", []),
        user_id=user_id,
    )

    # Store in SerenDB
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{SEREN_API_URL}/v1/tasks",
                json=task.to_dict(),
                headers={"Authorization": f"Bearer {SEREN_API_KEY}"},
                timeout=30.0,
            )

            if response.status_code in (200, 201):
                return ActionResult(status="created", result=task.to_dict())
            else:
                return ActionResult(
                    status="error",
                    reason=f"API error: {response.status_code} - {response.text}",
                )
    except httpx.HTTPError as e:
        return ActionResult(status="error", reason=str(e))


def complete_task(payload: dict, user_id: str) -> ActionResult:
    """Mark a task as completed.

    Args:
        payload: Contains task_id
        user_id: User ID

    Returns:
        ActionResult with completion status
    """
    task_id = payload.get("task_id")
    if not task_id:
        return ActionResult(status="error", reason="Missing task_id")

    update_data = {
        "status": TaskStatus.COMPLETED.value,
        "completed_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    try:
        with httpx.Client() as client:
            response = client.patch(
                f"{SEREN_API_URL}/v1/tasks/{task_id}",
                json=update_data,
                headers={"Authorization": f"Bearer {SEREN_API_KEY}"},
                timeout=30.0,
            )

            if response.status_code == 200:
                return ActionResult(status="completed", result={"task_id": task_id})
            else:
                return ActionResult(
                    status="error",
                    reason=f"API error: {response.status_code}",
                )
    except httpx.HTTPError as e:
        return ActionResult(status="error", reason=str(e))


def reschedule_task(payload: dict, user_id: str) -> ActionResult:
    """Reschedule a task to a new due date.

    Args:
        payload: Contains task_id and new_due_date
        user_id: User ID

    Returns:
        ActionResult with reschedule status
    """
    task_id = payload.get("task_id")
    new_due_date = payload.get("new_due_date")

    if not task_id or not new_due_date:
        return ActionResult(status="error", reason="Missing task_id or new_due_date")

    update_data = {
        "due_date": new_due_date,
        "updated_at": datetime.utcnow().isoformat(),
    }

    try:
        with httpx.Client() as client:
            response = client.patch(
                f"{SEREN_API_URL}/v1/tasks/{task_id}",
                json=update_data,
                headers={"Authorization": f"Bearer {SEREN_API_KEY}"},
                timeout=30.0,
            )

            if response.status_code == 200:
                return ActionResult(
                    status="rescheduled",
                    result={"task_id": task_id, "new_due_date": new_due_date},
                )
            else:
                return ActionResult(
                    status="error",
                    reason=f"API error: {response.status_code}",
                )
    except httpx.HTTPError as e:
        return ActionResult(status="error", reason=str(e))


def update_task(payload: dict, user_id: str) -> ActionResult:
    """Update task fields.

    Args:
        payload: Contains task_id and fields to update
        user_id: User ID

    Returns:
        ActionResult with update status
    """
    task_id = payload.get("task_id")
    if not task_id:
        return ActionResult(status="error", reason="Missing task_id")

    # Extract updateable fields
    update_data = {"updated_at": datetime.utcnow().isoformat()}
    for field in ["title", "description", "priority", "status", "tags", "due_date"]:
        if field in payload:
            update_data[field] = payload[field]

    try:
        with httpx.Client() as client:
            response = client.patch(
                f"{SEREN_API_URL}/v1/tasks/{task_id}",
                json=update_data,
                headers={"Authorization": f"Bearer {SEREN_API_KEY}"},
                timeout=30.0,
            )

            if response.status_code == 200:
                return ActionResult(status="updated", result={"task_id": task_id})
            else:
                return ActionResult(
                    status="error",
                    reason=f"API error: {response.status_code}",
                )
    except httpx.HTTPError as e:
        return ActionResult(status="error", reason=str(e))


def delete_task(payload: dict, user_id: str) -> ActionResult:
    """Delete a task.

    Args:
        payload: Contains task_id
        user_id: User ID

    Returns:
        ActionResult with deletion status
    """
    task_id = payload.get("task_id")
    if not task_id:
        return ActionResult(status="error", reason="Missing task_id")

    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{SEREN_API_URL}/v1/tasks/{task_id}",
                headers={"Authorization": f"Bearer {SEREN_API_KEY}"},
                timeout=30.0,
            )

            if response.status_code in (200, 204):
                return ActionResult(status="deleted", result={"task_id": task_id})
            else:
                return ActionResult(
                    status="error",
                    reason=f"API error: {response.status_code}",
                )
    except httpx.HTTPError as e:
        return ActionResult(status="error", reason=str(e))


def create_reminder(payload: dict, user_id: str) -> ActionResult:
    """Create a reminder for a task.

    Args:
        payload: Contains task_id, remind_at, and channel
        user_id: User ID

    Returns:
        ActionResult with reminder details
    """
    task_id = payload.get("task_id")
    remind_at = payload.get("remind_at")

    if not task_id or not remind_at:
        return ActionResult(status="error", reason="Missing task_id or remind_at")

    reminder = Reminder(
        task_id=task_id,
        remind_at=datetime.fromisoformat(remind_at),
        channel=payload.get("channel", "push"),
    )

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{SEREN_API_URL}/v1/reminders",
                json=reminder.to_dict(),
                headers={"Authorization": f"Bearer {SEREN_API_KEY}"},
                timeout=30.0,
            )

            if response.status_code in (200, 201):
                return ActionResult(status="created", result=reminder.to_dict())
            else:
                return ActionResult(
                    status="error",
                    reason=f"API error: {response.status_code}",
                )
    except httpx.HTTPError as e:
        return ActionResult(status="error", reason=str(e))


def log_context(payload: dict, user_id: str) -> ActionResult:
    """Log context to Seren Notes for future reference.

    Args:
        payload: Contains note content and metadata
        user_id: User ID

    Returns:
        ActionResult with log status
    """
    content = payload.get("content", "")
    metadata = payload.get("metadata", {})

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{SEREN_API_URL}/v1/notes",
                json={
                    "content": content,
                    "metadata": metadata,
                    "user_id": user_id,
                    "created_at": datetime.utcnow().isoformat(),
                },
                headers={"Authorization": f"Bearer {SEREN_API_KEY}"},
                timeout=30.0,
            )

            if response.status_code in (200, 201):
                return ActionResult(status="logged", result={"content_length": len(content)})
            else:
                return ActionResult(
                    status="error",
                    reason=f"API error: {response.status_code}",
                )
    except httpx.HTTPError as e:
        return ActionResult(status="error", reason=str(e))


def log_execution(
    user_id: str,
    action_type: str,
    payload: dict,
    result: ActionResult,
    autonomy_level: AutonomyLevel,
) -> None:
    """Log action execution for audit trail.

    Args:
        user_id: User ID
        action_type: Type of action executed
        payload: Action payload
        result: Action result
        autonomy_level: Autonomy level used
    """
    log = ExecutionLog(
        user_id=user_id,
        action_type=action_type,
        payload=payload,
        result=result.to_dict(),
        autonomy_level=autonomy_level,
    )

    try:
        with httpx.Client() as client:
            client.post(
                f"{SEREN_API_URL}/v1/execution_logs",
                json=log.to_dict(),
                headers={"Authorization": f"Bearer {SEREN_API_KEY}"},
                timeout=10.0,
            )
    except httpx.HTTPError:
        # Don't fail the action if logging fails
        pass


def get_tasks(
    user_id: str,
    status: Optional[TaskStatus] = None,
    due_before: Optional[datetime] = None,
) -> List[Task]:
    """Retrieve tasks from SerenDB.

    Args:
        user_id: User ID
        status: Optional status filter
        due_before: Optional due date filter

    Returns:
        List of tasks matching criteria
    """
    params = {"user_id": user_id}
    if status:
        params["status"] = status.value
    if due_before:
        params["due_before"] = due_before.isoformat()

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SEREN_API_URL}/v1/tasks",
                params=params,
                headers={"Authorization": f"Bearer {SEREN_API_KEY}"},
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                return [Task.from_dict(t) for t in data.get("tasks", [])]
    except httpx.HTTPError:
        pass

    return []


def get_pending_reminders(user_id: str, until: datetime) -> List[Reminder]:
    """Get reminders due before a certain time.

    Args:
        user_id: User ID
        until: Get reminders due before this time

    Returns:
        List of pending reminders
    """
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SEREN_API_URL}/v1/reminders",
                params={
                    "user_id": user_id,
                    "due_before": until.isoformat(),
                    "sent": False,
                },
                headers={"Authorization": f"Bearer {SEREN_API_KEY}"},
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                reminders = []
                for r in data.get("reminders", []):
                    reminders.append(
                        Reminder(
                            id=r["id"],
                            task_id=r["task_id"],
                            remind_at=datetime.fromisoformat(r["remind_at"]),
                            channel=r.get("channel", "push"),
                            sent=r.get("sent", False),
                        )
                    )
                return reminders
    except httpx.HTTPError:
        pass

    return []
