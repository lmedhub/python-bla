"""The Celery app.

Worker: celery -A config.celery worker
Beat:   celery -A config.celery beat
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

# Job modules are listed, not autodiscovered, so it is plain what the worker runs.
app = Celery("taskmanager", include=["apps.tasks.interfaces.jobs"])
# Every CELERY_* Django setting configures Celery (config/settings/base.py).
app.config_from_object("django.conf:settings", namespace="CELERY")
