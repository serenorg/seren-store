# ABOUTME: Notification formatting and delivery for the Daily Workflow Agent.
# ABOUTME: Handles push, email, and digest notifications with quiet hours support.

import os
from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum
from typing import List, Optional

import httpx

from config import NotificationPreferences
from models import Priority, Task


class NotificationChannel(str, Enum):
    PUSH = "push"
    EMAIL = "email"
    DIGEST = "digest"


class NotificationTier(str, Enum):
    URGENT = "urgent"      # Immediate push + email
    HIGH = "high"          # Real-time push
    MEDIUM = "medium"      # Daily digest
    LOW = "low"            # Weekly summary


@dataclass
class Notification:
    """A notification to be sent to the user."""

    user_id: str
    title: str
    body: str
    tier: NotificationTier
    channel: NotificationChannel
    task_id: Optional[str] = None
    sent_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "title": self.title,
            "body": self.body,
            "tier": self.tier.value,
            "channel": self.channel.value,
            "task_id": self.task_id,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }


# API configuration
SEREN_API_URL = os.environ.get("SEREN_API_URL", "https://api.serendb.com")
SEREN_API_KEY = os.environ.get("SEREN_API_KEY", "")


def get_notification_tier(task: Task) -> NotificationTier:
    """Determine notification tier based on task priority and due date.

    Args:
        task: Task to evaluate

    Returns:
        Appropriate notification tier
    """
    now = datetime.utcnow()

    # Overdue urgent tasks get immediate notification
    if task.due_date and task.due_date < now:
        if task.priority == Priority.URGENT:
            return NotificationTier.URGENT
        return NotificationTier.HIGH

    # Priority-based tier
    tier_map = {
        Priority.URGENT: NotificationTier.URGENT,
        Priority.HIGH: NotificationTier.HIGH,
        Priority.MEDIUM: NotificationTier.MEDIUM,
        Priority.LOW: NotificationTier.LOW,
    }

    return tier_map.get(task.priority, NotificationTier.MEDIUM)


def get_channel_for_tier(
    tier: NotificationTier,
    preferences: NotificationPreferences,
    current_time: Optional[time] = None,
) -> NotificationChannel:
    """Determine notification channel based on tier and user preferences.

    Args:
        tier: Notification tier
        preferences: User notification preferences
        current_time: Current time (for quiet hours check)

    Returns:
        Appropriate notification channel
    """
    if current_time is None:
        current_time = datetime.utcnow().time()

    is_quiet = preferences.is_quiet_time(current_time)

    # During quiet hours, only urgent with override gets through
    if is_quiet:
        if tier == NotificationTier.URGENT and preferences.urgent_override:
            return NotificationChannel.PUSH
        return NotificationChannel.DIGEST

    # Normal hours tier mapping
    if tier == NotificationTier.URGENT:
        return NotificationChannel.PUSH  # Will also send email
    elif tier == NotificationTier.HIGH:
        return NotificationChannel.PUSH
    else:
        return NotificationChannel.DIGEST


def format_task_notification(task: Task, context: str = "reminder") -> tuple:
    """Format a task into notification title and body.

    Args:
        task: Task to format
        context: Context for notification (reminder, overdue, created)

    Returns:
        Tuple of (title, body)
    """
    if context == "overdue":
        days_overdue = (datetime.utcnow() - task.due_date).days if task.due_date else 0
        if days_overdue == 1:
            title = "Task overdue"
            body = f"'{task.title}' was due yesterday"
        else:
            title = "Task overdue"
            body = f"'{task.title}' is {days_overdue} days overdue"

    elif context == "due_soon":
        title = "Task due soon"
        if task.due_date:
            due_time = task.due_date.strftime("%I:%M %p")
            body = f"'{task.title}' is due at {due_time}"
        else:
            body = f"'{task.title}' is due soon"

    elif context == "created":
        title = "New task created"
        body = f"'{task.title}' has been added to your tasks"

    else:  # reminder
        title = "Task reminder"
        body = f"Don't forget: {task.title}"

    return title, body


def format_digest(
    overdue: List[Task],
    due_today: List[Task],
    upcoming: List[Task],
    completed_yesterday: List[Task],
) -> str:
    """Format tasks into a daily digest message.

    Args:
        overdue: List of overdue tasks
        due_today: List of tasks due today
        upcoming: List of upcoming tasks
        completed_yesterday: List of tasks completed yesterday

    Returns:
        Formatted digest string
    """
    now = datetime.utcnow()
    date_str = now.strftime("%A, %B %d")

    lines = [f"Your Day — {date_str}", ""]

    if overdue:
        lines.append("OVERDUE (action needed)")
        for task in overdue[:5]:
            days = (now - task.due_date).days if task.due_date else 0
            if days == 1:
                lines.append(f"  • {task.title} (1 day late)")
            else:
                lines.append(f"  • {task.title} ({days} days late)")
        lines.append("")

    if due_today:
        lines.append("DUE TODAY")
        for task in due_today[:10]:
            priority_marker = "!" if task.priority in (Priority.URGENT, Priority.HIGH) else ""
            lines.append(f"  • {task.title}{priority_marker}")
        lines.append("")

    if upcoming:
        lines.append("UPCOMING THIS WEEK")
        for task in upcoming[:5]:
            if task.due_date:
                day = task.due_date.strftime("%a")
                lines.append(f"  • {task.title} ({day})")
            else:
                lines.append(f"  • {task.title}")
        lines.append("")

    if completed_yesterday:
        lines.append("COMPLETED YESTERDAY")
        for task in completed_yesterday[:5]:
            lines.append(f"  ✓ {task.title}")
        lines.append("")

    if not any([overdue, due_today, upcoming, completed_yesterday]):
        lines.append("No tasks scheduled. Enjoy your day!")

    return "\n".join(lines)


def send_notification(notification: Notification) -> bool:
    """Send a notification through the appropriate channel.

    Args:
        notification: Notification to send

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{SEREN_API_URL}/v1/notifications",
                json=notification.to_dict(),
                headers={"Authorization": f"Bearer {SEREN_API_KEY}"},
                timeout=30.0,
            )
            return response.status_code in (200, 201)
    except httpx.HTTPError:
        return False


def send_push_notification(user_id: str, title: str, body: str, task_id: Optional[str] = None) -> bool:
    """Send a push notification.

    Args:
        user_id: User to notify
        title: Notification title
        body: Notification body
        task_id: Optional related task ID

    Returns:
        True if sent successfully
    """
    notification = Notification(
        user_id=user_id,
        title=title,
        body=body,
        tier=NotificationTier.HIGH,
        channel=NotificationChannel.PUSH,
        task_id=task_id,
        sent_at=datetime.utcnow(),
    )
    return send_notification(notification)


def send_email_notification(user_id: str, subject: str, body: str, task_id: Optional[str] = None) -> bool:
    """Send an email notification.

    Args:
        user_id: User to notify
        subject: Email subject
        body: Email body
        task_id: Optional related task ID

    Returns:
        True if sent successfully
    """
    notification = Notification(
        user_id=user_id,
        title=subject,
        body=body,
        tier=NotificationTier.URGENT,
        channel=NotificationChannel.EMAIL,
        task_id=task_id,
        sent_at=datetime.utcnow(),
    )
    return send_notification(notification)


def send_digest(user_id: str, digest_content: str) -> bool:
    """Send a daily digest.

    Args:
        user_id: User to send digest to
        digest_content: Formatted digest content

    Returns:
        True if sent successfully
    """
    notification = Notification(
        user_id=user_id,
        title="Daily Digest",
        body=digest_content,
        tier=NotificationTier.MEDIUM,
        channel=NotificationChannel.DIGEST,
        sent_at=datetime.utcnow(),
    )
    return send_notification(notification)


def notify_task_event(
    task: Task,
    event: str,
    preferences: NotificationPreferences,
) -> bool:
    """Send notification for a task event respecting user preferences.

    Args:
        task: Task that triggered the event
        event: Event type (created, overdue, due_soon, reminder)
        preferences: User notification preferences

    Returns:
        True if notification sent successfully
    """
    tier = get_notification_tier(task)
    channel = get_channel_for_tier(tier, preferences)
    title, body = format_task_notification(task, event)

    notification = Notification(
        user_id=task.user_id,
        title=title,
        body=body,
        tier=tier,
        channel=channel,
        task_id=task.id,
        sent_at=datetime.utcnow(),
    )

    success = send_notification(notification)

    # Urgent notifications also send email
    if tier == NotificationTier.URGENT and channel == NotificationChannel.PUSH:
        send_email_notification(task.user_id, title, body, task.id)

    return success
