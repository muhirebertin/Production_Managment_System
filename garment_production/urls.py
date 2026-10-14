"""Project-level URLs: they send each request to the right app."""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),                    # Dashboard home
    path("inventory/", include("inventory.urls")),                  # App 1
    path("production/", include("production.urls")),                # App 2
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("admin/", admin.site.urls),                                 # Django Admin
]
