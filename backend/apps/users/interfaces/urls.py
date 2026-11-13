from django.urls import path

from apps.users.interfaces.auth import LoginView, LogoutView, RefreshView
from apps.users.interfaces.views import MeView, UserListView

urlpatterns = [
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/refresh", RefreshView.as_view(), name="auth-refresh"),
    path("auth/logout", LogoutView.as_view(), name="auth-logout"),
    path("users", UserListView.as_view(), name="user-list"),
    path("users/me", MeView.as_view(), name="user-me"),
]
