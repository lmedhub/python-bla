from datetime import date

TITLE_MAX_LENGTH = 200


def clean_title(raw: str) -> str:
    raise NotImplementedError


def check_due_date_on_create(due_date: date | None, today: date) -> None:
    raise NotImplementedError
