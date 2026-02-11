# ABOUTME: Configuration for the Daily Workflow Agent.
# ABOUTME: Defines autonomy levels, notification preferences, and schedule settings.

from dataclasses import dataclass, field
from datetime import time
from typing import List, Tuple

from models import AutonomyLevel


@dataclass
class AutonomyConfig:
    """User-configurable autonomy levels per action type."""

    # Task management
    create_task: AutonomyLevel = AutonomyLevel.AUTO
    complete_task: AutonomyLevel = AutonomyLevel.CONFIRM
    reschedule_task: AutonomyLevel = AutonomyLevel.SUGGEST

    # Calendar
    create_event: AutonomyLevel = AutonomyLevel.SUGGEST  # Never auto
    modify_event: AutonomyLevel = AutonomyLevel.CONFIRM

    # Email
    draft_reply: AutonomyLevel = AutonomyLevel.SUGGEST
    send_reply: AutonomyLevel = AutonomyLevel.MANUAL  # Always requires human approval

    # Notifications
    send_reminder: AutonomyLevel = AutonomyLevel.AUTO

    # Context logging
    log_context: AutonomyLevel = AutonomyLevel.AUTO

    def get_level(self, action_type: str) -> AutonomyLevel:
        """Get autonomy level for an action type."""
        return getattr(self, action_type, AutonomyLevel.SUGGEST)

    def to_dict(self) -> dict:
        return {
            "create_task": self.create_task.value,
            "complete_task": self.complete_task.value,
            "reschedule_task": self.reschedule_task.value,
            "create_event": self.create_event.value,
            "modify_event": self.modify_event.value,
            "draft_reply": self.draft_reply.value,
            "send_reply": self.send_reply.value,
            "send_reminder": self.send_reminder.value,
            "log_context": self.log_context.value,
        }


@dataclass
class NotificationPreferences:
    """User-configurable notification settings."""

    quiet_hours: Tuple[time, time] = field(default_factory=lambda: (time(22, 0), time(7, 0)))
    digest_time: time = field(default_factory=lambda: time(7, 0))
    urgent_override: bool = True  # Push even during quiet hours
    channels: List[str] = field(default_factory=lambda: ["push", "email"])

    def is_quiet_time(self, current_time: time) -> bool:
        """Check if current time is within quiet hours."""
        start, end = self.quiet_hours
        if start <= end:
            return start <= current_time <= end
        # Quiet hours span midnight
        return current_time >= start or current_time <= end

    def to_dict(self) -> dict:
        return {
            "quiet_hours": [self.quiet_hours[0].isoformat(), self.quiet_hours[1].isoformat()],
            "digest_time": self.digest_time.isoformat(),
            "urgent_override": self.urgent_override,
            "channels": self.channels,
        }


@dataclass
class SchedulePreferences:
    """User-configurable schedule settings."""

    digest_time: str = "07:00"
    reminder_frequency: str = "hourly"  # hourly, every_2h, every_4h
    overdue_checks: List[str] = field(default_factory=lambda: ["09:00", "14:00", "18:00"])
    timezone: str = "America/Los_Angeles"

    def to_dict(self) -> dict:
        return {
            "digest_time": self.digest_time,
            "reminder_frequency": self.reminder_frequency,
            "overdue_checks": self.overdue_checks,
            "timezone": self.timezone,
        }


@dataclass
class UserPreferences:
    """Complete user preferences combining all settings."""

    user_id: str
    autonomy: AutonomyConfig = field(default_factory=AutonomyConfig)
    notifications: NotificationPreferences = field(default_factory=NotificationPreferences)
    schedule: SchedulePreferences = field(default_factory=SchedulePreferences)

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "autonomy": self.autonomy.to_dict(),
            "notifications": self.notifications.to_dict(),
            "schedule": self.schedule.to_dict(),
        }


# Scheduled jobs for Seren-Cron
SCHEDULED_JOBS = [
    {
        "id": "morning_digest",
        "schedule": "0 7 * * *",  # Daily 7:00 AM
        "payload": {"type": "digest"},
        "description": "Generate and send morning digest",
    },
    {
        "id": "reminder_check",
        "schedule": "0 * * * *",  # Every hour
        "payload": {"type": "check_reminders"},
        "description": "Check for due reminders",
    },
    {
        "id": "overdue_scan",
        "schedule": "0 9,14,18 * * *",  # 9am, 2pm, 6pm
        "payload": {"type": "scan_overdue"},
        "description": "Flag overdue tasks",
    },
]


# Model routing for cost optimization
# Uses OpenRouter model IDs via Seren Models publisher
MODEL_ROUTING = {
    # Routine tasks - use Haiku (~$0.0015/call)
    "task_extraction": "anthropic/claude-3.5-haiku",
    "deduplication": "anthropic/claude-3.5-haiku",
    "reminder_formatting": "anthropic/claude-3.5-haiku",
    "calendar_prep": "anthropic/claude-3.5-haiku",
    # Complex reasoning - use Sonnet (~$0.005/call)
    "priority_decision": "anthropic/claude-sonnet-4",
    "conflict_resolution": "anthropic/claude-sonnet-4",
    "learning": "anthropic/claude-sonnet-4",
}


def get_model_for_task(task_type: str) -> str:
    """Get appropriate model for a task type."""
    return MODEL_ROUTING.get(task_type, "anthropic/claude-3.5-haiku")
