"""Errors shared by every feature. The API maps each one to a single HTTP status."""

from typing import Self


class DomainError(Exception):
    """Base for errors caused by the request, not by a bug."""


class InvalidInputError(DomainError):
    """400. `fields` maps an API field name to its messages."""

    def __init__(self, fields: dict[str, list[str]]) -> None:
        super().__init__(fields)
        self.fields = fields

    @classmethod
    def on(cls, field: str, message: str) -> Self:
        return cls({field: [message]})


class PermissionDeniedError(DomainError):
    """403."""


class NotFoundError(DomainError):
    """404."""
