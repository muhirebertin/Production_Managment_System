from django.db.models import Count, Sum
from django.shortcuts import render

from inventory.models import Product, RawMaterial
from production.models import Machine, ProductionLine, ProductionOrder, Worker


def dashboard(request):
    """Dashboard home page: summary cards, charts and tables."""
    orders = ProductionOrder.objects.select_related("product", "line")
    active_orders = orders.exclude(status="CANCELLED")

    # Summary cards
    total_orders = active_orders.count()
    completed = active_orders.filter(status="COMPLETED").count()
    completion_rate = round(completed * 100 / total_orders, 1) if total_orders else 0
    units_produced = active_orders.aggregate(total=Sum("quantity_produced", default=0))["total"]
    low_stock = [m for m in RawMaterial.objects.all() if m.is_low_stock]

    # Chart 1: units ordered vs produced per product (the database adds them up)
    per_product = (Product.objects
                   .annotate(ordered=Sum("orders__quantity"), produced=Sum("orders__quantity_produced"))
                   .filter(ordered__gt=0).order_by("code"))

    # Chart 2: number of orders in each status
    status_counts = dict(orders.values_list("status").annotate(n=Count("id")))
    status_labels = [label for code, label in ProductionOrder.STATUS_CHOICES]
    status_values = [status_counts.get(code, 0) for code, label in ProductionOrder.STATUS_CHOICES]

    # Progress of each production line on its open orders (planned + in progress)
    lines = list(ProductionLine.objects.annotate(
        num_machines=Count("machines", distinct=True),
        num_workers=Count("workers", distinct=True)))
    for line in lines:
        totals = line.orders.filter(status__in=["PLANNED", "IN_PROGRESS"]).aggregate(
            ordered=Sum("quantity", default=0), produced=Sum("quantity_produced", default=0))
        line.open_ordered = totals["ordered"]
        line.open_produced = totals["produced"]
        line.progress = round(totals["produced"] * 100 / totals["ordered"]) if totals["ordered"] else 0

    context = {
        "total_orders": total_orders,
        "in_progress": active_orders.filter(status="IN_PROGRESS").count(),
        "completion_rate": completion_rate,
        "units_produced": units_produced,
        "low_stock": low_stock,
        "active_machines": Machine.objects.filter(status="ACTIVE").count(),
        "total_machines": Machine.objects.count(),
        "total_workers": Worker.objects.count(),
        "total_products": Product.objects.count(),
        "recent_orders": orders.order_by("-id")[:5],
        "overdue_orders": [o for o in orders if o.is_overdue],
        "lines": lines,
        # data for the charts
        "product_labels": [p.name for p in per_product],
        "product_ordered": [p.ordered for p in per_product],
        "product_produced": [p.produced for p in per_product],
        "status_labels": status_labels,
        "status_values": status_values,
    }
    return render(request, "dashboard.html", context)
