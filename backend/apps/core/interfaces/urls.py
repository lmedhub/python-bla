from django.db import transaction
from django.urls import path

from apps.core.interfaces.health import HealthView

urlpatterns = [
    # No request transaction: with ATOMIC_REQUESTS, Django would connect to the database
    # before the view runs, and a database outage would become a 500 instead of a 503.
    path("health", transaction.non_atomic_requests(HealthView.as_view()), name="health"),
]
