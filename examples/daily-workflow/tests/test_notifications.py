# ABOUTME: Tests for Daily Workflow Agent notification system.
# ABOUTME: Covers notification formatting, tier determination, and channel selection.

from datetime import datetime, time, timedelta

import pytest

from config import NotificationPreferences
from models import Priority, Task, TaskStatus
from notifications import (
    Notification,
    NotificationChannel,
    NotificationTier,
    format_digest,
    format_task_notification,
    get_channel_for_tier,
    get_notification_tier,
)


class TestNotificationTier:
    """Tests for notification tier determination."""

    def test_overdue_urgent_gets_urgent_tier(self, overdue_task):
        """Overdue urgent tasks should get URGENT tier."""
        overdue_task.priority = Priority.URGENT
        tier = get_notification_tier(overdue_task)
        assert tier == NotificationTier.URGENT

    def test_overdue_non_urgent_gets_high_tier(self, overdue_task):
        """Overdue non-urgent tasks should get HIGH tier."""
        tier = get_notification_tier(overdue_task)
        assert tier == NotificationTier.HIGH

    def test_urgent_priority_gets_urgent_tier(self, urgent_task):
        """Urgent priority tasks should get URGENT tier."""
        tier = get_notification_tier(urgent_task)
        assert tier == NotificationTier.URGENT

    def test_medium_priority_gets_medium_tier(self, sample_task):
        """Medium priority tasks should get MEDIUM tier."""
        tier = get_notification_tier(sample_task)
        assert tier == NotificationTier.MEDIUM

    def test_low_priority_gets_low_tier(self, sample_task):
        """Low priority tasks should get LOW tier."""
        sample_task.priority = Priority.LOW
        tier = get_notification_tier(sample_task)
        assert tier == NotificationTier.LOW


class TestChannelSelection:
    """Tests for notification channel selection."""

    def test_urgent_during_normal_hours_gets_push(self, default_notification_prefs):
        """Urgent notifications during normal hours should use push."""
        channel = get_channel_for_tier(
            NotificationTier.URGENT,
            default_notification_prefs,
            current_time=time(10, 0),  # 10am
        )
        assert channel == NotificationChannel.PUSH

    def test_high_during_normal_hours_gets_push(self, default_notification_prefs):
        """High priority during normal hours should use push."""
        channel = get_channel_for_tier(
            NotificationTier.HIGH,
            default_notification_prefs,
            current_time=time(14, 0),  # 2pm
        )
        assert channel == NotificationChannel.PUSH

    def test_medium_gets_digest(self, default_notification_prefs):
        """Medium priority should use digest."""
        channel = get_channel_for_tier(
            NotificationTier.MEDIUM,
            default_notification_prefs,
            current_time=time(10, 0),
        )
        assert channel == NotificationChannel.DIGEST

    def test_quiet_hours_non_urgent_gets_digest(self, default_notification_prefs):
        """Non-urgent during quiet hours should use digest."""
        channel = get_channel_for_tier(
            NotificationTier.HIGH,
            default_notification_prefs,
            current_time=time(23, 0),  # 11pm
        )
        assert channel == NotificationChannel.DIGEST

    def test_quiet_hours_urgent_with_override_gets_push(self, default_notification_prefs):
        """Urgent with override during quiet hours should use push."""
        channel = get_channel_for_tier(
            NotificationTier.URGENT,
            default_notification_prefs,
            current_time=time(3, 0),  # 3am
        )
        assert channel == NotificationChannel.PUSH

    def test_quiet_hours_urgent_without_override_gets_digest(self):
        """Urgent without override during quiet hours should use digest."""
        prefs = NotificationPreferences(urgent_override=False)
        channel = get_channel_for_tier(
            NotificationTier.URGENT,
            prefs,
            current_time=time(3, 0),
        )
        assert channel == NotificationChannel.DIGEST


class TestTaskNotificationFormatting:
    """Tests for task notification formatting."""

    def test_format_overdue_notification(self, overdue_task):
        """Overdue notification should include days overdue."""
        title, body = format_task_notification(overdue_task, "overdue")

        assert title == "Task overdue"
        assert "2 days overdue" in body or "days overdue" in body

    def test_format_due_soon_notification(self, sample_task):
        """Due soon notification should include time."""
        title, body = format_task_notification(sample_task, "due_soon")

        assert title == "Task due soon"
        assert sample_task.title in body

    def test_format_created_notification(self, sample_task):
        """Created notification should confirm task creation."""
        title, body = format_task_notification(sample_task, "created")

        assert title == "New task created"
        assert sample_task.title in body

    def test_format_reminder_notification(self, sample_task):
        """Reminder notification should include task title."""
        title, body = format_task_notification(sample_task, "reminder")

        assert title == "Task reminder"
        assert sample_task.title in body


class TestDigestFormatting:
    """Tests for daily digest formatting."""

    def test_format_empty_digest(self):
        """Empty digest should indicate no tasks."""
        digest = format_digest([], [], [], [])

        assert "No tasks scheduled" in digest

    def test_format_digest_with_overdue(self, overdue_task):
        """Digest should show overdue section."""
        digest = format_digest([overdue_task], [], [], [])

        assert "OVERDUE" in digest
        assert overdue_task.title in digest
        assert "late" in digest.lower()

    def test_format_digest_with_due_today(self, sample_task):
        """Digest should show due today section."""
        sample_task.due_date = datetime.utcnow().replace(hour=17, minute=0)
        digest = format_digest([], [sample_task], [], [])

        assert "DUE TODAY" in digest
        assert sample_task.title in digest

    def test_format_digest_with_upcoming(self, sample_task):
        """Digest should show upcoming section."""
        sample_task.due_date = datetime.utcnow() + timedelta(days=3)
        digest = format_digest([], [], [sample_task], [])

        assert "UPCOMING" in digest
        assert sample_task.title in digest

    def test_format_digest_with_completed(self, completed_task):
        """Digest should show completed section."""
        digest = format_digest([], [], [], [completed_task])

        assert "COMPLETED" in digest
        assert completed_task.title in digest
        assert "✓" in digest

    def test_format_digest_includes_date(self):
        """Digest should include current date."""
        digest = format_digest([], [], [], [])
        now = datetime.utcnow()

        assert now.strftime("%A") in digest or now.strftime("%B") in digest

    def test_format_digest_urgent_marked(self, urgent_task):
        """Urgent tasks in digest should have priority marker."""
        urgent_task.due_date = datetime.utcnow().replace(hour=17, minute=0)
        digest = format_digest([], [urgent_task], [], [])

        assert "!" in digest


class TestNotificationModel:
    """Tests for Notification model."""

    def test_notification_creation(self):
        """Notification should be created with required fields."""
        notification = Notification(
            user_id="user-123",
            title="Test",
            body="Test body",
            tier=NotificationTier.MEDIUM,
            channel=NotificationChannel.PUSH,
        )

        assert notification.user_id == "user-123"
        assert notification.title == "Test"
        assert notification.tier == NotificationTier.MEDIUM

    def test_notification_to_dict(self):
        """Notification should serialize correctly."""
        notification = Notification(
            user_id="user-123",
            title="Test",
            body="Test body",
            tier=NotificationTier.HIGH,
            channel=NotificationChannel.EMAIL,
            task_id="task-456",
            sent_at=datetime.utcnow(),
        )
        data = notification.to_dict()

        assert data["user_id"] == "user-123"
        assert data["tier"] == "high"
        assert data["channel"] == "email"
        assert data["task_id"] == "task-456"
        assert data["sent_at"] is not None
