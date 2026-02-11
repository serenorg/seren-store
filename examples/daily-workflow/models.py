# ABOUTME: Data models for the Daily Workflow Agent.
# ABOUTME: Defines Task, Reminder, Signal, and ActionResult structures.

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Any
import uuid


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEFERRED = "deferred"


class SignalSource(str, Enum):
    EMAIL = "email"
    CALENDAR = "calendar"
    MANUAL = "manual"
    AUTO = "auto"


class AutonomyLevel(str, Enum):
    AUTO = "auto"          # Execute immediately, log for review
    SUGGEST = "suggest"    # Propose action, await approval
    CONFIRM = "confirm"    # Queue action, ask before executing
    MANUAL = "manual"      # Feature available but agent won't trigger


@dataclass
class Task:
    """A task to be completed by the user."""

    title: str
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    source: SignalSource = SignalSource.MANUAL
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    follow_up_from: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = field(default_factory=lambda: datetime.utcnow())
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for storage/transmission."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "priority": self.priority.value,
            "status": self.status.value,
            "tags": self.tags,
            "source": self.source.value,
            "follow_up_from": self.follow_up_from,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create Task from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            user_id=data.get("user_id", ""),
            title=data["title"],
            description=data.get("description"),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            priority=Priority(data.get("priority", "medium")),
            status=TaskStatus(data.get("status", "pending")),
            tags=data.get("tags", []),
            source=SignalSource(data.get("source", "manual")),
            follow_up_from=data.get("follow_up_from"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )


@dataclass
class Reminder:
    """A reminder for a task."""

    task_id: str
    remind_at: datetime
    channel: str = "push"  # push, email, digest
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sent: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "remind_at": self.remind_at.isoformat(),
            "channel": self.channel,
            "sent": self.sent,
        }


@dataclass
class Signal:
    """An incoming signal from email, calendar, or manual input."""

    source: SignalSource
    payload: dict
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    received_at: datetime = field(default_factory=lambda: datetime.utcnow())
    processed: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "source": self.source.value,
            "payload": self.payload,
            "received_at": self.received_at.isoformat(),
            "processed": self.processed,
        }


@dataclass
class ActionResult:
    """Result of an action execution."""

    status: str  # created, updated, skipped, pending_approval, error
    result: Optional[Any] = None
    reason: Optional[str] = None
    proposal: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "result": self.result,
            "reason": self.reason,
            "proposal": self.proposal,
        }


@dataclass
class ExecutionLog:
    """Audit trail for agent actions."""

    user_id: str
    action_type: str
    payload: dict
    result: dict
    autonomy_level: AutonomyLevel
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_override: Optional[dict] = None
    timestamp: datetime = field(default_factory=lambda: datetime.utcnow())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action_type": self.action_type,
            "payload": self.payload,
            "result": self.result,
            "autonomy_level": self.autonomy_level.value,
            "user_override": self.user_override,
            "timestamp": self.timestamp.isoformat(),
        }
