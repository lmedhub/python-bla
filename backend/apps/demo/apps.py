from django.apps import AppConfig


class DemoConfig(AppConfig):
    """Demo data only. It may use every feature; no feature may use it (import-linter)."""

    name = "apps.demo"
    label = "demo"
