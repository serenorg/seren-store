# ABOUTME: Tests for Daily Workflow Agent data models.
# ABOUTME: Covers Task, Reminder, Signal, and ActionResult serialization.

from datetime import datetime, timedelta

import pytest

from models import (
    ActionResult,
    AutonomyLevel,
    ExecutionLog,
    Priority,
    Reminder,
    Signal,
    SignalSource,
    Task,
    TaskStatus,
)


class TestTask:
    """Tests for Task model."""

    def test_task_creation_defaults(self):
        """Task should have sensible defaults."""
        task = Task(title="Test task")

        assert task.title == "Test task"
        assert task.priority == Priority.MEDIUM
        assert task.status == TaskStatus.PENDING
        assert task.source == SignalSource.MANUAL
        assert task.id is not None
        assert task.created_at is not None
        assert task.tags == []

    def test_task_to_dict(self, sample_task):
        """Task should serialize to dict correctly."""
        data = sample_task.to_dict()

        assert data["id"] == "task-123"
        assert data["user_id"] == "user-456"
        assert data["title"] == "Send pricing doc"
        assert data["priority"] == "medium"
        assert data["status"] == "pending"
        assert data["tags"] == ["sales", "acme"]
        assert data["source"] == "email"
        assert "created_at" in data
        assert "due_date" in data

    def test_task_from_dict(self):
        """Task should deserialize from dict correctly."""
        data = {
            "id": "task-abc",
            "user_id": "user-xyz",
            "title": "Review contract",
            "priority": "high",
            "status": "in_progress",
            "tags": ["legal"],
            "source": "manual",
            "created_at": "2026-01-20T10:00:00",
            "updated_at": "2026-01-20T10:00:00",
        }

        task = Task.from_dict(data)

        assert task.id == "task-abc"
        assert task.title == "Review contract"
        assert task.priority == Priority.HIGH
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.tags == ["legal"]

    def test_task_roundtrip(self, sample_task):
        """Task should survive roundtrip serialization."""
        data = sample_task.to_dict()
        restored = Task.from_dict(data)

        assert restored.id == sample_task.id
        assert restored.title == sample_task.title
        assert restored.priority == sample_task.priority


class TestReminder:
    """Tests for Reminder model."""

    def test_reminder_creation(self):
        """Reminder should be created with required fields."""
        remind_at = datetime.utcnow() + timedelta(hours=2)
        reminder = Reminder(task_id="task-123", remind_at=remind_at)

        assert reminder.task_id == "task-123"
        assert reminder.remind_at == remind_at
        assert reminder.channel == "push"
        assert reminder.sent is False

    def test_reminder_to_dict(self, sample_reminder):
        """Reminder should serialize correctly."""
        data = sample_reminder.to_dict()

        assert data["task_id"] == "task-123"
        assert "remind_at" in data
        assert data["channel"] == "push"
        assert data["sent"] is False


class TestSignal:
    """Tests for Signal model."""

    def test_signal_creation(self):
        """Signal should be created with source and payload."""
        signal = Signal(
            source=SignalSource.EMAIL,
            payload={"from": "test@example.com", "subject": "Test"},
            user_id="user-123",
        )

        assert signal.source == SignalSource.EMAIL
        assert signal.payload["from"] == "test@example.com"
        assert signal.processed is False

    def test_signal_to_dict(self):
        """Signal should serialize correctly."""
        signal = Signal(
            source=SignalSource.CALENDAR,
            payload={"title": "Meeting"},
            user_id="user-123",
        )
        data = signal.to_dict()

        assert data["source"] == "calendar"
        assert data["payload"]["title"] == "Meeting"
        assert data["processed"] is False


class TestActionResult:
    """Tests for ActionResult model."""

    def test_action_result_success(self):
        """ActionResult should represent success."""
        result = ActionResult(status="created", result={"task_id": "123"})

        assert result.status == "created"
        assert result.result == {"task_id": "123"}
        assert result.reason is None

    def test_action_result_error(self):
        """ActionResult should represent error."""
        result = ActionResult(status="error", reason="API timeout")

        assert result.status == "error"
        assert result.reason == "API timeout"

    def test_action_result_pending_approval(self):
        """ActionResult should represent pending approval."""
        proposal = {"title": "New task", "priority": "high"}
        result = ActionResult(status="pending_approval", proposal=proposal)

        assert result.status == "pending_approval"
        assert result.proposal == proposal


class TestExecutionLog:
    """Tests for ExecutionLog model."""

    def test_execution_log_creation(self):
        """ExecutionLog should capture action execution."""
        log = ExecutionLog(
            user_id="user-123",
            action_type="create_task",
            payload={"title": "Test"},
            result={"status": "created"},
            autonomy_level=AutonomyLevel.AUTO,
        )

        assert log.user_id == "user-123"
        assert log.action_type == "create_task"
        assert log.autonomy_level == AutonomyLevel.AUTO

    def test_execution_log_to_dict(self):
        """ExecutionLog should serialize correctly."""
        log = ExecutionLog(
            user_id="user-123",
            action_type="complete_task",
            payload={"task_id": "task-456"},
            result={"status": "completed"},
            autonomy_level=AutonomyLevel.CONFIRM,
        )
        data = log.to_dict()

        assert data["action_type"] == "complete_task"
        assert data["autonomy_level"] == "confirm"
        assert "timestamp" in data


class TestEnums:
    """Tests for enum values."""

    def test_priority_values(self):
        """Priority enum should have expected values."""
        assert Priority.LOW.value == "low"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.HIGH.value == "high"
        assert Priority.URGENT.value == "urgent"

    def test_task_status_values(self):
        """TaskStatus enum should have expected values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.DEFERRED.value == "deferred"

    def test_autonomy_level_values(self):
        """AutonomyLevel enum should have expected values."""
        assert AutonomyLevel.AUTO.value == "auto"
        assert AutonomyLevel.SUGGEST.value == "suggest"
        assert AutonomyLevel.CONFIRM.value == "confirm"
        assert AutonomyLevel.MANUAL.value == "manual"
