from django.apps import AppConfig


class TasksConfig(AppConfig):
    name = "apps.tasks.infrastructure"
    label = "tasks"
    default_auto_field = "django.db.models.BigAutoField"
