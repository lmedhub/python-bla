from django.urls import include, path

urlpatterns = [
    path("api/v1/", include("apps.core.interfaces.urls")),
    path("api/v1/", include("apps.users.interfaces.urls")),
]

# JSON instead of Django's HTML pages, so every error has the same shape.
handler404 = "apps.core.interfaces.errors.not_found_view"
handler500 = "apps.core.interfaces.errors.server_error_view"
