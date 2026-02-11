# ABOUTME: Tests for Daily Workflow Agent action execution.
# ABOUTME: Covers task CRUD operations with mocked HTTP responses.

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import json

import pytest

from config import AutonomyConfig
from models import AutonomyLevel, Priority, TaskStatus


class TestExecuteAction:
    """Tests for action execution dispatch."""

    def test_manual_autonomy_skips_action(self, default_autonomy_config):
        """Manual autonomy level should skip action."""
        from actions import execute_action

        # Set all actions to manual
        config = AutonomyConfig(
            create_task=AutonomyLevel.MANUAL,
            complete_task=AutonomyLevel.MANUAL,
        )

        result = execute_action("create_task", {"title": "Test"}, config, "user-123")

        assert result.status == "skipped"
        assert result.reason == "manual_mode"

    def test_suggest_autonomy_returns_pending_approval(self, default_autonomy_config):
        """Suggest autonomy level should return pending approval."""
        from actions import execute_action

        config = AutonomyConfig(create_task=AutonomyLevel.SUGGEST)
        payload = {"title": "Test task"}

        result = execute_action("create_task", payload, config, "user-123")

        assert result.status == "pending_approval"
        assert result.proposal == payload

    def test_unknown_action_returns_error(self):
        """Unknown action type should return error when autonomy allows execution."""
        from actions import execute_action

        # Use AUTO autonomy so action proceeds to handler lookup
        config = AutonomyConfig()
        # Manually set unknown action to AUTO to bypass suggest
        setattr(config, "unknown_action", AutonomyLevel.AUTO)

        result = execute_action("unknown_action", {}, config, "user-123")

        assert result.status == "error"
        assert "Unknown action" in result.reason


class TestCreateTask:
    """Tests for task creation."""

    @patch('actions.httpx.Client')
    def test_create_task_success(self, mock_httpx):
        """Task creation should succeed with valid data."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "task-new"}
        mock_client.post.return_value = mock_response
        mock_httpx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.return_value.__exit__ = MagicMock(return_value=False)

        from actions import create_task

        result = create_task(
            {"title": "New task", "priority": "high"},
            "user-123"
        )

        assert result.status == "created"
        assert result.result["title"] == "New task"

    @patch('actions.httpx.Client')
    def test_create_task_api_error(self, mock_httpx):
        """Task creation should handle API errors."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_client.post.return_value = mock_response
        mock_httpx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.return_value.__exit__ = MagicMock(return_value=False)

        from actions import create_task

        result = create_task({"title": "Test"}, "user-123")

        assert result.status == "error"
        assert "500" in result.reason


class TestCompleteTask:
    """Tests for task completion."""

    @patch('actions.httpx.Client')
    def test_complete_task_success(self, mock_httpx):
        """Task completion should succeed."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.patch.return_value = mock_response
        mock_httpx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.return_value.__exit__ = MagicMock(return_value=False)

        from actions import complete_task

        result = complete_task({"task_id": "task-123"}, "user-123")

        assert result.status == "completed"
        assert result.result["task_id"] == "task-123"

    def test_complete_task_missing_id(self):
        """Task completion should fail without task_id."""
        from actions import complete_task

        result = complete_task({}, "user-123")

        assert result.status == "error"
        assert "Missing task_id" in result.reason


class TestRescheduleTask:
    """Tests for task rescheduling."""

    @patch('actions.httpx.Client')
    def test_reschedule_task_success(self, mock_httpx):
        """Task rescheduling should succeed."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.patch.return_value = mock_response
        mock_httpx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.return_value.__exit__ = MagicMock(return_value=False)

        from actions import reschedule_task

        result = reschedule_task(
            {"task_id": "task-123", "new_due_date": "2026-01-30T17:00:00"},
            "user-123"
        )

        assert result.status == "rescheduled"
        assert result.result["new_due_date"] == "2026-01-30T17:00:00"

    def test_reschedule_task_missing_fields(self):
        """Task rescheduling should fail without required fields."""
        from actions import reschedule_task

        result = reschedule_task({"task_id": "task-123"}, "user-123")

        assert result.status == "error"
        assert "Missing" in result.reason


class TestUpdateTask:
    """Tests for task updates."""

    @patch('actions.httpx.Client')
    def test_update_task_success(self, mock_httpx):
        """Task update should succeed."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.patch.return_value = mock_response
        mock_httpx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.return_value.__exit__ = MagicMock(return_value=False)

        from actions import update_task

        result = update_task(
            {"task_id": "task-123", "title": "Updated title", "priority": "urgent"},
            "user-123"
        )

        assert result.status == "updated"

    def test_update_task_missing_id(self):
        """Task update should fail without task_id."""
        from actions import update_task

        result = update_task({"title": "New title"}, "user-123")

        assert result.status == "error"
        assert "Missing task_id" in result.reason


class TestDeleteTask:
    """Tests for task deletion."""

    @patch('actions.httpx.Client')
    def test_delete_task_success(self, mock_httpx):
        """Task deletion should succeed."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_client.delete.return_value = mock_response
        mock_httpx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.return_value.__exit__ = MagicMock(return_value=False)

        from actions import delete_task

        result = delete_task({"task_id": "task-123"}, "user-123")

        assert result.status == "deleted"

    def test_delete_task_missing_id(self):
        """Task deletion should fail without task_id."""
        from actions import delete_task

        result = delete_task({}, "user-123")

        assert result.status == "error"


class TestCreateReminder:
    """Tests for reminder creation."""

    @patch('actions.httpx.Client')
    def test_create_reminder_success(self, mock_httpx):
        """Reminder creation should succeed."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_client.post.return_value = mock_response
        mock_httpx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.return_value.__exit__ = MagicMock(return_value=False)

        from actions import create_reminder

        remind_at = (datetime.utcnow() + timedelta(hours=2)).isoformat()
        result = create_reminder(
            {"task_id": "task-123", "remind_at": remind_at, "channel": "push"},
            "user-123"
        )

        assert result.status == "created"

    def test_create_reminder_missing_fields(self):
        """Reminder creation should fail without required fields."""
        from actions import create_reminder

        result = create_reminder({"task_id": "task-123"}, "user-123")

        assert result.status == "error"
        assert "Missing" in result.reason


class TestGetTasks:
    """Tests for task retrieval."""

    @patch('actions.httpx.Client')
    def test_get_tasks_success(self, mock_httpx):
        """Task retrieval should return tasks."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tasks": [
                {
                    "id": "task-1",
                    "title": "Task 1",
                    "priority": "medium",
                    "status": "pending",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ]
        }
        mock_client.get.return_value = mock_response
        mock_httpx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.return_value.__exit__ = MagicMock(return_value=False)

        from actions import get_tasks

        tasks = get_tasks("user-123")

        assert len(tasks) == 1
        assert tasks[0].title == "Task 1"

    @patch('actions.httpx.Client')
    def test_get_tasks_with_status_filter(self, mock_httpx):
        """Task retrieval should accept status filter."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tasks": []}
        mock_client.get.return_value = mock_response
        mock_httpx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.return_value.__exit__ = MagicMock(return_value=False)

        from actions import get_tasks

        get_tasks("user-123", status=TaskStatus.PENDING)

        # Verify status was passed in params
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["status"] == "pending"

    @patch('actions.httpx.Client')
    def test_get_tasks_empty_on_error(self, mock_httpx):
        """Task retrieval should return empty list on error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_client.get.return_value = mock_response
        mock_httpx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.return_value.__exit__ = MagicMock(return_value=False)

        from actions import get_tasks

        tasks = get_tasks("user-123")

        assert tasks == []


class TestGetPendingReminders:
    """Tests for reminder retrieval."""

    @patch('actions.httpx.Client')
    def test_get_pending_reminders_success(self, mock_httpx):
        """Reminder retrieval should return reminders."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "reminders": [
                {
                    "id": "reminder-1",
                    "task_id": "task-123",
                    "remind_at": datetime.utcnow().isoformat(),
                    "channel": "push",
                    "sent": False,
                }
            ]
        }
        mock_client.get.return_value = mock_response
        mock_httpx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.return_value.__exit__ = MagicMock(return_value=False)

        from actions import get_pending_reminders

        reminders = get_pending_reminders("user-123", datetime.utcnow())

        assert len(reminders) == 1
        assert reminders[0].task_id == "task-123"


class TestLogContext:
    """Tests for context logging."""

    @patch('actions.httpx.Client')
    def test_log_context_success(self, mock_httpx):
        """Context logging should succeed."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_client.post.return_value = mock_response
        mock_httpx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.return_value.__exit__ = MagicMock(return_value=False)

        from actions import log_context

        result = log_context(
            {"content": "User prefers morning meetings", "metadata": {"type": "preference"}},
            "user-123"
        )

        assert result.status == "logged"
