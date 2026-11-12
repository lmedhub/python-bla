from datetime import date, timedelta

import pytest

from apps.core.domain.errors import InvalidInputError
from apps.tasks.domain.rules import TITLE_MAX_LENGTH, check_due_date_on_create, clean_title

TODAY = date(2026, 11, 12)


class TestCleanTitle:
    def test_trims_surrounding_whitespace(self):
        assert clean_title("  Write tests \n") == "Write tests"

    @pytest.mark.parametrize("raw", ["", "   ", "\t\n"])
    def test_rejects_blank_titles(self, raw: str):
        with pytest.raises(InvalidInputError) as error:
            clean_title(raw)

        assert list(error.value.fields) == ["title"]

    def test_accepts_the_maximum_length(self):
        title = "x" * TITLE_MAX_LENGTH

        assert clean_title(title) == title

    def test_rejects_one_character_over_the_maximum(self):
        with pytest.raises(InvalidInputError) as error:
            clean_title("x" * (TITLE_MAX_LENGTH + 1))

        assert list(error.value.fields) == ["title"]

    def test_measures_length_after_trimming(self):
        title = "x" * TITLE_MAX_LENGTH

        assert clean_title(f"  {title}  ") == title


class TestDueDateOnCreate:
    def test_rejects_a_date_before_today(self):
        with pytest.raises(InvalidInputError) as error:
            check_due_date_on_create(TODAY - timedelta(days=1), today=TODAY)

        assert list(error.value.fields) == ["due_date"]

    @pytest.mark.parametrize("due_date", [TODAY, TODAY + timedelta(days=30), None])
    def test_accepts_today_a_future_date_or_no_date(self, due_date: date | None):
        check_due_date_on_create(due_date, today=TODAY)
