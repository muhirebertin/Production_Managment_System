from django.contrib import admin

from .models import Machine, ProductionLine, ProductionOrder, Worker


@admin.register(ProductionLine)
class ProductionLineAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "daily_capacity")


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "machine_type", "line", "status")
    list_filter = ("line", "status", "machine_type")
    search_fields = ("code", "name")


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ("employee_no", "first_name", "last_name", "role", "line", "user")
    list_filter = ("role", "line")
    search_fields = ("employee_no", "first_name", "last_name")


@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ("order_no", "product", "line", "quantity", "quantity_produced", "status", "due_date")
    list_filter = ("status", "line")
    search_fields = ("order_no",)
