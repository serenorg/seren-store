# ABOUTME: Pytest fixtures for Daily Workflow Agent tests.
# ABOUTME: Provides common test data and mocked dependencies.

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Priority, Task, TaskStatus, Reminder, SignalSource
from config import AutonomyConfig, NotificationPreferences, UserPreferences


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        id="task-123",
        user_id="user-456",
        title="Send pricing doc",
        description="Send the pricing document to Acme Corp",
        priority=Priority.MEDIUM,
        status=TaskStatus.PENDING,
        due_date=datetime.utcnow() + timedelta(days=2),
        tags=["sales", "acme"],
        source=SignalSource.EMAIL,
    )


@pytest.fixture
def overdue_task():
    """Create an overdue task for testing."""
    return Task(
        id="task-overdue",
        user_id="user-456",
        title="Reply to investor",
        priority=Priority.HIGH,
        status=TaskStatus.PENDING,
        due_date=datetime.utcnow() - timedelta(days=2),
        source=SignalSource.EMAIL,
    )


@pytest.fixture
def urgent_task():
    """Create an urgent task for testing."""
    return Task(
        id="task-urgent",
        user_id="user-456",
        title="Emergency client call",
        priority=Priority.URGENT,
        status=TaskStatus.PENDING,
        due_date=datetime.utcnow() + timedelta(hours=1),
        source=SignalSource.MANUAL,
    )


@pytest.fixture
def completed_task():
    """Create a completed task for testing."""
    return Task(
        id="task-done",
        user_id="user-456",
        title="Submit report",
        priority=Priority.MEDIUM,
        status=TaskStatus.COMPLETED,
        completed_at=datetime.utcnow() - timedelta(hours=5),
        source=SignalSource.MANUAL,
    )


@pytest.fixture
def sample_reminder(sample_task):
    """Create a sample reminder for testing."""
    return Reminder(
        id="reminder-123",
        task_id=sample_task.id,
        remind_at=datetime.utcnow() + timedelta(hours=1),
        channel="push",
    )


@pytest.fixture
def sample_email_payload():
    """Create a sample email payload for testing."""
    return {
        "from": "john@example.com",
        "subject": "Meeting follow-up",
        "body": "Thanks for the demo! Can you send the pricing doc by Friday? Also loop in Sarah for the technical review.",
    }


@pytest.fixture
def sample_calendar_payload():
    """Create a sample calendar event payload for testing."""
    return {
        "title": "Product Demo",
        "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "attendees": ["john@example.com", "sarah@example.com"],
        "description": "Demo of the new features to the sales team",
    }


@pytest.fixture
def default_autonomy_config():
    """Create default autonomy configuration."""
    return AutonomyConfig()


@pytest.fixture
def default_notification_prefs():
    """Create default notification preferences."""
    return NotificationPreferences()


@pytest.fixture
def user_preferences():
    """Create complete user preferences."""
    return UserPreferences(user_id="user-456")


@pytest.fixture
def mock_anthropic_client():
    """Create a mocked Anthropic client."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='[]')]
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_httpx_client():
    """Create a mocked httpx client."""
    with patch('httpx.Client') as mock:
        client_instance = MagicMock()
        mock.return_value.__enter__ = MagicMock(return_value=client_instance)
        mock.return_value.__exit__ = MagicMock(return_value=False)
        yield client_instance
