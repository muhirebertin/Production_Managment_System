"""App-level URLs for the production app."""
from django.urls import path

from . import views

app_name = "production"

urlpatterns = [
    # Production lines
    path("lines/", views.line_list, name="line_list"),
    path("lines/add/", views.line_create, name="line_create"),
    path("lines/<int:pk>/", views.line_detail, name="line_detail"),
    path("lines/<int:pk>/edit/", views.line_update, name="line_update"),
    path("lines/<int:pk>/delete/", views.line_delete, name="line_delete"),
    # Machines
    path("machines/", views.machine_list, name="machine_list"),
    path("machines/add/", views.machine_create, name="machine_create"),
    path("machines/<int:pk>/", views.machine_detail, name="machine_detail"),
    path("machines/<int:pk>/edit/", views.machine_update, name="machine_update"),
    path("machines/<int:pk>/delete/", views.machine_delete, name="machine_delete"),
    # Workers
    path("workers/", views.worker_list, name="worker_list"),
    path("workers/add/", views.worker_create, name="worker_create"),
    path("workers/<int:pk>/", views.worker_detail, name="worker_detail"),
    path("workers/<int:pk>/edit/", views.worker_update, name="worker_update"),
    path("workers/<int:pk>/delete/", views.worker_delete, name="worker_delete"),
    # Production orders
    path("orders/", views.order_list, name="order_list"),
    path("orders/add/", views.order_create, name="order_create"),
    path("orders/status/<str:status>/", views.orders_by_status, name="orders_by_status"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/<int:pk>/edit/", views.order_update, name="order_update"),
    path("orders/<int:pk>/delete/", views.order_delete, name="order_delete"),
]
