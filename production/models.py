from datetime import date

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from inventory.models import Product


class ProductionLine(models.Model):
    """A group of machines and workers on the factory floor, e.g. 'Line A - Shirts'."""
    name = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=100)
    daily_capacity = models.PositiveIntegerField(
        "Daily capacity (units)", validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Machine(models.Model):
    """A machine belongs to ONE production line (ForeignKey)."""
    TYPE_CHOICES = [("CUTTING", "Cutting"), ("SEWING", "Sewing"), ("OVERLOCK", "Overlock"),
                    ("PRESSING", "Pressing"), ("EMBROIDERY", "Embroidery")]
    STATUS_CHOICES = [("ACTIVE", "Active"), ("MAINTENANCE", "Under maintenance"), ("IDLE", "Idle")]

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    machine_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    line = models.ForeignKey(ProductionLine, on_delete=models.PROTECT, related_name="machines")
    status = models.CharField(max_length=11, choices=STATUS_CHOICES, default="ACTIVE")

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Worker(models.Model):
    """A worker is assigned to ONE line and can have ONE login account (OneToOne)."""
    ROLE_CHOICES = [("SUPERVISOR", "Supervisor"), ("OPERATOR", "Machine operator"),
                    ("QC", "Quality inspector")]

    employee_no = models.CharField("Employee number", max_length=10, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=10)
    line = models.ForeignKey(ProductionLine, on_delete=models.PROTECT, related_name="workers")
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name="worker_profile")

    class Meta:
        ordering = ["employee_no"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class ProductionOrder(models.Model):
    """An order to produce a quantity of ONE product on ONE line, led by ONE supervisor."""
    STATUS_CHOICES = [("PLANNED", "Planned"), ("IN_PROGRESS", "In progress"),
                      ("COMPLETED", "Completed"), ("CANCELLED", "Cancelled")]

    order_no = models.CharField("Order number", max_length=12, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="orders")
    line = models.ForeignKey(ProductionLine, on_delete=models.PROTECT, related_name="orders")
    supervisor = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="supervised_orders")
    quantity = models.PositiveIntegerField("Quantity to produce", validators=[MinValueValidator(1)])
    quantity_produced = models.PositiveIntegerField(default=0)
    start_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=11, choices=STATUS_CHOICES, default="PLANNED")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date", "-order_no"]

    def __str__(self):
        return f"{self.order_no} - {self.product.name} x {self.quantity}"

    @property
    def progress(self):
        """Percentage of the order already produced."""
        return round(self.quantity_produced * 100 / self.quantity) if self.quantity else 0

    @property
    def is_overdue(self):
        return self.status in ("PLANNED", "IN_PROGRESS") and self.due_date < date.today()

    def material_requirements(self):
        """Materials needed for the units still to produce, compared with the stock."""
        remaining = self.quantity - self.quantity_produced
        rows = []
        for item in self.product.bom_items.select_related("material"):
            needed = item.quantity_per_unit * remaining
            rows.append({"material": item.material, "needed": round(needed, 2),
                         "in_stock": item.material.quantity_in_stock,
                         "enough": item.material.quantity_in_stock >= needed})
        return rows
