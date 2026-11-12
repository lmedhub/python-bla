from datetime import date

from apps.core.domain.errors import InvalidInputError

TITLE_MAX_LENGTH = 200


def clean_title(raw: str) -> str:
    title = raw.strip()
    if not title:
        raise InvalidInputError.on("title", "This field may not be blank.")
    if len(title) > TITLE_MAX_LENGTH:
        raise InvalidInputError.on(
            "title", f"Ensure this field has no more than {TITLE_MAX_LENGTH} characters."
        )
    return title


def check_due_date_on_create(due_date: date | None, today: date) -> None:
    # Only on create: an existing task may legitimately become (or be edited while) overdue.
    if due_date is not None and due_date < today:
        raise InvalidInputError.on("due_date", "Due date cannot be in the past.")
