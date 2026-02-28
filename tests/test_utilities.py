"""Tests for utility functions (parsers, formatters, helpers)."""

from datetime import date, timedelta
from unittest.mock import patch

from app.routers.contacts import parse_role, parse_name, format_phone_for_voice, format_role_for_voice
from app.routers.todos import (
    parse_natural_date,
    format_date_for_voice,
    parse_status,
    parse_priority,
    format_status_for_voice,
    format_priority_for_voice,
)
from app.models.contact import ContactRole
from app.models.todo import TodoStatus, TodoPriority


# ---- Contact Utilities ----

class TestParseRole:
    def test_direct_roles(self):
        assert parse_role("lawyer") == ContactRole.LAWYER
        assert parse_role("buyer") == ContactRole.BUYER
        assert parse_role("seller") == ContactRole.SELLER
        assert parse_role("contractor") == ContactRole.CONTRACTOR

    def test_aliases(self):
        assert parse_role("attorney") == ContactRole.LAWYER
        assert parse_role("mortgage") == ContactRole.MORTGAGE_BROKER
        assert parse_role("bank") == ContactRole.LENDER
        assert parse_role("renter") == ContactRole.TENANT
        assert parse_role("pm") == ContactRole.PROPERTY_MANAGER
        assert parse_role("home inspector") == ContactRole.INSPECTOR
        assert parse_role("home stager") == ContactRole.STAGER

    def test_case_insensitive(self):
        assert parse_role("LAWYER") == ContactRole.LAWYER
        assert parse_role("Attorney") == ContactRole.LAWYER

    def test_unknown_defaults_other(self):
        assert parse_role("unknown_role") == ContactRole.OTHER
        assert parse_role("xyz") == ContactRole.OTHER

    def test_whitespace_handling(self):
        assert parse_role("  lawyer  ") == ContactRole.LAWYER


class TestParseName:
    def test_single_name(self):
        full, first, last = parse_name("Madonna")
        assert full == "Madonna"
        assert first == "Madonna"
        assert last is None

    def test_two_names(self):
        full, first, last = parse_name("John Doe")
        assert full == "John Doe"
        assert first == "John"
        assert last == "Doe"

    def test_three_names(self):
        full, first, last = parse_name("John Michael Doe")
        assert full == "John Michael Doe"
        assert first == "John"
        assert last == "Michael Doe"

    def test_whitespace(self):
        full, first, last = parse_name("  John   Doe  ")
        assert first == "John"


class TestFormatPhoneForVoice:
    def test_ten_digits(self):
        result = format_phone_for_voice("2013355555")
        assert result == "201, 335, 5555"

    def test_formatted_phone(self):
        result = format_phone_for_voice("201-335-5555")
        assert result == "201, 335, 5555"

    def test_short_phone(self):
        result = format_phone_for_voice("555-1234")
        # Less than 10 digits, returned as-is
        assert result == "555-1234"


class TestFormatRoleForVoice:
    def test_single_word(self):
        assert format_role_for_voice(ContactRole.LAWYER) == "lawyer"

    def test_underscore_role(self):
        assert format_role_for_voice(ContactRole.MORTGAGE_BROKER) == "mortgage broker"
        assert format_role_for_voice(ContactRole.TITLE_COMPANY) == "title company"
        assert format_role_for_voice(ContactRole.PROPERTY_MANAGER) == "property manager"


# ---- Todo Utilities ----

class TestParseNaturalDate:
    def test_today(self):
        result = parse_natural_date("today")
        assert result == date.today()

    def test_tomorrow(self):
        result = parse_natural_date("tomorrow")
        assert result == date.today() + timedelta(days=1)

    def test_yesterday(self):
        result = parse_natural_date("yesterday")
        assert result == date.today() - timedelta(days=1)

    def test_day_names(self):
        result = parse_natural_date("monday")
        assert result is not None
        assert result.weekday() == 0  # Monday

        result = parse_natural_date("friday")
        assert result is not None
        assert result.weekday() == 4  # Friday

    def test_day_abbreviations(self):
        result = parse_natural_date("mon")
        assert result is not None
        assert result.weekday() == 0

        result = parse_natural_date("fri")
        assert result is not None
        assert result.weekday() == 4

    def test_next_day(self):
        result = parse_natural_date("next monday")
        assert result is not None
        assert result.weekday() == 0
        # "next monday" should be at least 7 days away
        assert (result - date.today()).days >= 7

    def test_in_x_days(self):
        result = parse_natural_date("in 3 days")
        assert result == date.today() + timedelta(days=3)

    def test_in_x_weeks(self):
        result = parse_natural_date("in 2 weeks")
        assert result == date.today() + timedelta(weeks=2)

    def test_next_week(self):
        result = parse_natural_date("next week")
        assert result == date.today() + timedelta(weeks=1)

    def test_this_day(self):
        result = parse_natural_date("this friday")
        assert result is not None
        assert result.weekday() == 4

    def test_empty_string(self):
        assert parse_natural_date("") is None

    def test_none(self):
        assert parse_natural_date(None) is None

    def test_unparseable(self):
        # gibberish that dateutil can't handle may return None
        result = parse_natural_date("xyzzy123")
        # Could be None or could be parsed by dateutil fuzzy
        # Just verify it doesn't crash
        assert result is None or isinstance(result, date)


class TestFormatDateForVoice:
    def test_today(self):
        assert format_date_for_voice(date.today()) == "today"

    def test_tomorrow(self):
        assert format_date_for_voice(date.today() + timedelta(days=1)) == "tomorrow"

    def test_yesterday(self):
        assert format_date_for_voice(date.today() - timedelta(days=1)) == "yesterday"

    def test_this_week(self):
        # 3 days from now should show day name
        future = date.today() + timedelta(days=3)
        result = format_date_for_voice(future)
        assert result in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def test_next_week(self):
        future = date.today() + timedelta(days=10)
        result = format_date_for_voice(future)
        assert result.startswith("next ")

    def test_far_future(self):
        future = date.today() + timedelta(days=60)
        result = format_date_for_voice(future)
        # Should be like "April 29"
        assert any(month in result for month in [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ])


class TestParseStatus:
    def test_direct_statuses(self):
        assert parse_status("pending") == TodoStatus.PENDING
        assert parse_status("completed") == TodoStatus.COMPLETED
        assert parse_status("in_progress") == TodoStatus.IN_PROGRESS
        assert parse_status("cancelled") == TodoStatus.CANCELLED

    def test_aliases(self):
        assert parse_status("done") == TodoStatus.COMPLETED
        assert parse_status("finished") == TodoStatus.COMPLETED
        assert parse_status("complete") == TodoStatus.COMPLETED
        assert parse_status("todo") == TodoStatus.PENDING
        assert parse_status("not started") == TodoStatus.PENDING
        assert parse_status("working on") == TodoStatus.IN_PROGRESS
        assert parse_status("doing") == TodoStatus.IN_PROGRESS

    def test_case_insensitive(self):
        assert parse_status("DONE") == TodoStatus.COMPLETED
        assert parse_status("Pending") == TodoStatus.PENDING

    def test_unknown_defaults_pending(self):
        assert parse_status("xyz") == TodoStatus.PENDING


class TestParsePriority:
    def test_direct_priorities(self):
        assert parse_priority("low") == TodoPriority.LOW
        assert parse_priority("medium") == TodoPriority.MEDIUM
        assert parse_priority("high") == TodoPriority.HIGH
        assert parse_priority("urgent") == TodoPriority.URGENT

    def test_aliases(self):
        assert parse_priority("normal") == TodoPriority.MEDIUM
        assert parse_priority("important") == TodoPriority.HIGH
        assert parse_priority("critical") == TodoPriority.URGENT
        assert parse_priority("asap") == TodoPriority.URGENT

    def test_unknown_defaults_medium(self):
        assert parse_priority("xyz") == TodoPriority.MEDIUM


class TestFormatStatusForVoice:
    def test_simple(self):
        assert format_status_for_voice(TodoStatus.PENDING) == "pending"
        assert format_status_for_voice(TodoStatus.COMPLETED) == "completed"

    def test_underscore(self):
        assert format_status_for_voice(TodoStatus.IN_PROGRESS) == "in progress"


class TestFormatPriorityForVoice:
    def test_all_priorities(self):
        assert format_priority_for_voice(TodoPriority.LOW) == "low"
        assert format_priority_for_voice(TodoPriority.MEDIUM) == "medium"
        assert format_priority_for_voice(TodoPriority.HIGH) == "high"
        assert format_priority_for_voice(TodoPriority.URGENT) == "urgent"
