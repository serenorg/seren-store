# ABOUTME: Tests for Daily Workflow Agent signal processing.
# ABOUTME: Covers email/calendar task extraction and duplicate detection.

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import json

import pytest

from models import Priority, SignalSource, Task


class TestProcessSignal:
    """Tests for signal processing dispatch."""

    def test_email_signal_dispatches_to_email_handler(self, sample_email_payload):
        """Email signals should be processed by email handler."""
        with patch('signals.extract_from_email') as mock_extract:
            mock_extract.return_value = []
            from signals import process_signal

            process_signal("email", sample_email_payload, "user-123")

            mock_extract.assert_called_once_with(sample_email_payload, "user-123")

    def test_calendar_signal_dispatches_to_calendar_handler(self, sample_calendar_payload):
        """Calendar signals should be processed by calendar handler."""
        with patch('signals.extract_from_calendar') as mock_extract:
            mock_extract.return_value = []
            from signals import process_signal

            process_signal("calendar", sample_calendar_payload, "user-123")

            mock_extract.assert_called_once_with(sample_calendar_payload, "user-123")

    def test_manual_signal_creates_task(self):
        """Manual signals should create a task directly."""
        from signals import process_signal

        payload = {
            "title": "Review contract",
            "priority": "high",
            "due_date": "2026-01-25T17:00:00",
        }

        tasks = process_signal("manual", payload, "user-123")

        assert len(tasks) == 1
        assert tasks[0].title == "Review contract"
        assert tasks[0].priority == Priority.HIGH
        assert tasks[0].source == SignalSource.MANUAL

    def test_unknown_signal_returns_empty(self):
        """Unknown signal types should return empty list."""
        from signals import process_signal

        tasks = process_signal("unknown", {}, "user-123")

        assert tasks == []


class TestManualTaskCreation:
    """Tests for manual task creation."""

    def test_create_manual_task_with_all_fields(self):
        """Manual task should be created with all provided fields."""
        from signals import create_manual_task

        payload = {
            "title": "Write report",
            "description": "Q4 financial report",
            "priority": "urgent",
            "due_date": "2026-01-30T09:00:00",
            "tags": ["finance", "q4"],
        }

        task = create_manual_task(payload, "user-123")

        assert task.title == "Write report"
        assert task.description == "Q4 financial report"
        assert task.priority == Priority.URGENT
        assert task.tags == ["finance", "q4"]
        assert task.user_id == "user-123"

    def test_create_manual_task_with_defaults(self):
        """Manual task should use defaults for missing fields."""
        from signals import create_manual_task

        payload = {"title": "Quick task"}

        task = create_manual_task(payload, "user-123")

        assert task.title == "Quick task"
        assert task.priority == Priority.MEDIUM
        assert task.tags == []
        assert task.due_date is None

    def test_create_manual_task_invalid_date_ignored(self):
        """Invalid due date should be ignored."""
        from signals import create_manual_task

        payload = {
            "title": "Task",
            "due_date": "not-a-date",
        }

        task = create_manual_task(payload, "user-123")

        assert task.due_date is None


class TestEmailExtraction:
    """Tests for email task extraction with mocked LLM."""

    @patch('signals.get_seren_claude_client')
    def test_extract_from_email_parses_json_response(self, mock_get_client, sample_email_payload):
        """Email extraction should parse LLM JSON response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps([
            {"title": "Send pricing doc", "priority": "medium", "due_date": "2026-01-24", "tags": ["sales"]}
        ]))]
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        from signals import extract_from_email

        tasks = extract_from_email(sample_email_payload, "user-123")

        assert len(tasks) == 1
        assert tasks[0].title == "Send pricing doc"
        assert tasks[0].source == SignalSource.EMAIL

    @patch('signals.get_seren_claude_client')
    def test_extract_from_email_handles_markdown_code_blocks(self, mock_get_client, sample_email_payload):
        """Email extraction should handle markdown-wrapped JSON."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="""```json
[{"title": "Follow up", "priority": "low"}]
```""")]
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        from signals import extract_from_email

        tasks = extract_from_email(sample_email_payload, "user-123")

        assert len(tasks) == 1
        assert tasks[0].title == "Follow up"

    @patch('signals.get_seren_claude_client')
    def test_extract_from_email_returns_empty_on_invalid_json(self, mock_get_client, sample_email_payload):
        """Email extraction should return empty list on invalid JSON."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is not JSON")]
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        from signals import extract_from_email

        tasks = extract_from_email(sample_email_payload, "user-123")

        assert tasks == []

    @patch('signals.get_seren_claude_client')
    def test_extract_from_email_empty_array_response(self, mock_get_client, sample_email_payload):
        """Email extraction should handle empty array response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="[]")]
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        from signals import extract_from_email

        tasks = extract_from_email(sample_email_payload, "user-123")

        assert tasks == []


class TestCalendarExtraction:
    """Tests for calendar task extraction with mocked LLM."""

    @patch('signals.get_seren_claude_client')
    def test_extract_from_calendar_creates_prep_tasks(self, mock_get_client, sample_calendar_payload):
        """Calendar extraction should create prep tasks."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps([
            {"title": "Prepare demo slides", "priority": "high", "tags": ["demo"]}
        ]))]
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        from signals import extract_from_calendar

        tasks = extract_from_calendar(sample_calendar_payload, "user-123")

        assert len(tasks) == 1
        assert tasks[0].title == "Prepare demo slides"
        assert tasks[0].source == SignalSource.CALENDAR
        assert "meeting-prep" in tasks[0].tags

    @patch('signals.get_seren_claude_client')
    def test_extract_from_calendar_sets_due_before_event(self, mock_get_client, sample_calendar_payload):
        """Calendar prep tasks should be due before the event."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps([
            {"title": "Review agenda", "priority": "medium"}
        ]))]
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        from signals import extract_from_calendar

        tasks = extract_from_calendar(sample_calendar_payload, "user-123")

        assert len(tasks) == 1
        assert tasks[0].due_date is not None
        # Due date should be before the event
        event_time = datetime.fromisoformat(sample_calendar_payload["start_time"])
        assert tasks[0].due_date < event_time


class TestDuplicateDetection:
    """Tests for task duplicate detection."""

    def test_check_duplicate_no_existing_tasks(self, sample_task):
        """No duplicates when no existing tasks."""
        from signals import check_duplicate

        result = check_duplicate(sample_task, [])

        assert result is None

    @patch('signals.get_seren_claude_client')
    def test_check_duplicate_finds_match(self, mock_get_client, sample_task):
        """Duplicate detection should find matching task."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="0")]  # Index of match
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        from signals import check_duplicate

        existing = Task(title="Send pricing document", user_id="user-123")
        result = check_duplicate(sample_task, [existing])

        assert result == existing

    @patch('signals.get_seren_claude_client')
    def test_check_duplicate_no_match(self, mock_get_client, sample_task):
        """Duplicate detection should return None when no match."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="-1")]  # No match
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        from signals import check_duplicate

        existing = Task(title="Completely different task", user_id="user-123")
        result = check_duplicate(sample_task, [existing])

        assert result is None


class TestSignalClassification:
    """Tests for signal classification."""

    @patch('signals.get_seren_claude_client')
    def test_classify_actionable_email(self, mock_get_client):
        """Actionable email should be classified correctly."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "actionable": True,
            "priority": "high",
            "reason": "Contains request for pricing doc"
        }))]
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        from signals import classify_signal

        result = classify_signal("email", {"subject": "Need pricing", "body": "Send doc"})

        assert result["actionable"] is True
        assert result["priority"] == "high"

    @patch('signals.get_seren_claude_client')
    def test_classify_informational_email(self, mock_get_client):
        """Informational email should be classified as non-actionable."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "actionable": False,
            "priority": "low",
            "reason": "Just an FYI"
        }))]
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        from signals import classify_signal

        result = classify_signal("email", {"subject": "FYI", "body": "No action needed"})

        assert result["actionable"] is False
