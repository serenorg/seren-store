# ABOUTME: Tests for Daily Workflow Agent configuration.
# ABOUTME: Covers autonomy config, notification preferences, and model routing.

from datetime import time

import pytest

from config import (
    AutonomyConfig,
    NotificationPreferences,
    SchedulePreferences,
    UserPreferences,
    SCHEDULED_JOBS,
    MODEL_ROUTING,
    get_model_for_task,
)
from models import AutonomyLevel


class TestAutonomyConfig:
    """Tests for AutonomyConfig."""

    def test_default_autonomy_levels(self, default_autonomy_config):
        """Default autonomy levels should match design spec."""
        config = default_autonomy_config

        assert config.create_task == AutonomyLevel.AUTO
        assert config.complete_task == AutonomyLevel.CONFIRM
        assert config.reschedule_task == AutonomyLevel.SUGGEST
        assert config.create_event == AutonomyLevel.SUGGEST
        assert config.send_reply == AutonomyLevel.MANUAL

    def test_get_level_known_action(self, default_autonomy_config):
        """get_level should return correct level for known actions."""
        config = default_autonomy_config

        assert config.get_level("create_task") == AutonomyLevel.AUTO
        assert config.get_level("send_reply") == AutonomyLevel.MANUAL

    def test_get_level_unknown_action(self, default_autonomy_config):
        """get_level should return SUGGEST for unknown actions."""
        config = default_autonomy_config

        assert config.get_level("unknown_action") == AutonomyLevel.SUGGEST

    def test_to_dict(self, default_autonomy_config):
        """Config should serialize to dict."""
        data = default_autonomy_config.to_dict()

        assert data["create_task"] == "auto"
        assert data["send_reply"] == "manual"
        assert len(data) == 9  # All action types


class TestNotificationPreferences:
    """Tests for NotificationPreferences."""

    def test_default_quiet_hours(self, default_notification_prefs):
        """Default quiet hours should be 10pm to 7am."""
        prefs = default_notification_prefs

        assert prefs.quiet_hours[0] == time(22, 0)
        assert prefs.quiet_hours[1] == time(7, 0)

    def test_is_quiet_time_during_quiet_hours(self, default_notification_prefs):
        """is_quiet_time should return True during quiet hours."""
        prefs = default_notification_prefs

        # 11pm is during quiet hours (22:00 - 07:00)
        assert prefs.is_quiet_time(time(23, 0)) is True
        # 3am is during quiet hours
        assert prefs.is_quiet_time(time(3, 0)) is True

    def test_is_quiet_time_outside_quiet_hours(self, default_notification_prefs):
        """is_quiet_time should return False outside quiet hours."""
        prefs = default_notification_prefs

        # 9am is outside quiet hours
        assert prefs.is_quiet_time(time(9, 0)) is False
        # 3pm is outside quiet hours
        assert prefs.is_quiet_time(time(15, 0)) is False

    def test_urgent_override_default(self, default_notification_prefs):
        """Urgent override should be True by default."""
        assert default_notification_prefs.urgent_override is True

    def test_default_channels(self, default_notification_prefs):
        """Default channels should include push and email."""
        assert "push" in default_notification_prefs.channels
        assert "email" in default_notification_prefs.channels


class TestSchedulePreferences:
    """Tests for SchedulePreferences."""

    def test_default_digest_time(self):
        """Default digest time should be 7am."""
        prefs = SchedulePreferences()
        assert prefs.digest_time == "07:00"

    def test_default_reminder_frequency(self):
        """Default reminder frequency should be hourly."""
        prefs = SchedulePreferences()
        assert prefs.reminder_frequency == "hourly"

    def test_default_overdue_checks(self):
        """Default overdue checks should be at 9am, 2pm, 6pm."""
        prefs = SchedulePreferences()
        assert prefs.overdue_checks == ["09:00", "14:00", "18:00"]

    def test_to_dict(self):
        """SchedulePreferences should serialize correctly."""
        prefs = SchedulePreferences()
        data = prefs.to_dict()

        assert data["digest_time"] == "07:00"
        assert data["timezone"] == "America/Los_Angeles"


class TestUserPreferences:
    """Tests for UserPreferences."""

    def test_user_preferences_creation(self, user_preferences):
        """UserPreferences should combine all settings."""
        prefs = user_preferences

        assert prefs.user_id == "user-456"
        assert isinstance(prefs.autonomy, AutonomyConfig)
        assert isinstance(prefs.notifications, NotificationPreferences)
        assert isinstance(prefs.schedule, SchedulePreferences)

    def test_user_preferences_to_dict(self, user_preferences):
        """UserPreferences should serialize all nested configs."""
        data = user_preferences.to_dict()

        assert data["user_id"] == "user-456"
        assert "autonomy" in data
        assert "notifications" in data
        assert "schedule" in data


class TestScheduledJobs:
    """Tests for scheduled job configuration."""

    def test_morning_digest_job(self):
        """Morning digest job should be configured correctly."""
        digest_job = next(j for j in SCHEDULED_JOBS if j["id"] == "morning_digest")

        assert digest_job["schedule"] == "0 7 * * *"
        assert digest_job["payload"]["type"] == "digest"

    def test_reminder_check_job(self):
        """Reminder check job should run hourly."""
        reminder_job = next(j for j in SCHEDULED_JOBS if j["id"] == "reminder_check")

        assert reminder_job["schedule"] == "0 * * * *"
        assert reminder_job["payload"]["type"] == "check_reminders"

    def test_overdue_scan_job(self):
        """Overdue scan should run at 9am, 2pm, 6pm."""
        overdue_job = next(j for j in SCHEDULED_JOBS if j["id"] == "overdue_scan")

        assert overdue_job["schedule"] == "0 9,14,18 * * *"


class TestModelRouting:
    """Tests for LLM model routing."""

    def test_haiku_for_routine_tasks(self):
        """Routine tasks should use Haiku."""
        assert "haiku" in MODEL_ROUTING["task_extraction"]
        assert "haiku" in MODEL_ROUTING["deduplication"]
        assert "haiku" in MODEL_ROUTING["reminder_formatting"]

    def test_sonnet_for_complex_reasoning(self):
        """Complex reasoning should use Sonnet."""
        assert "sonnet" in MODEL_ROUTING["priority_decision"]
        assert "sonnet" in MODEL_ROUTING["conflict_resolution"]

    def test_get_model_for_task_known(self):
        """get_model_for_task should return configured model."""
        model = get_model_for_task("task_extraction")
        assert "haiku" in model

    def test_get_model_for_task_unknown(self):
        """get_model_for_task should default to Haiku for unknown tasks."""
        model = get_model_for_task("unknown_task_type")
        assert "haiku" in model
