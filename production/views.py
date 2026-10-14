from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MachineForm, ProductionLineForm, ProductionOrderForm, WorkerForm
from .models import Machine, ProductionLine, ProductionOrder, Worker


# ---------------- Production lines ----------------

def line_list(request):
    lines = ProductionLine.objects.prefetch_related("machines", "workers", "orders")
    return render(request, "production/line_list.html", {"lines": lines})


def line_detail(request, pk):
    line = get_object_or_404(ProductionLine, pk=pk)
    return render(request, "production/line_detail.html", {
        "line": line,
        "machines": line.machines.all(),
        "workers": line.workers.all(),
        "orders": line.orders.select_related("product"),
    })


@login_required
def line_create(request):
    form = ProductionLineForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Production line added successfully.")
        return redirect("production:line_list")
    return render(request, "form.html", {"form": form, "title": "Add Production Line",
                                         "cancel_url": "production:line_list"})


@login_required
def line_update(request, pk):
    line = get_object_or_404(ProductionLine, pk=pk)
    form = ProductionLineForm(request.POST or None, instance=line)
    if form.is_valid():
        form.save()
        messages.success(request, "Production line updated successfully.")
        return redirect("production:line_detail", pk=line.pk)
    return render(request, "form.html", {"form": form, "title": "Edit Production Line",
                                         "cancel_url": "production:line_list"})


@login_required
def line_delete(request, pk):
    line = get_object_or_404(ProductionLine, pk=pk)
    if request.method == "POST":
        try:
            line.delete()
            messages.success(request, "Production line deleted successfully.")
        except ProtectedError:
            messages.error(request, "Cannot delete: this line still has machines, workers or orders.")
        return redirect("production:line_list")
    return render(request, "confirm_delete.html", {"object": line,
                                                   "cancel_url": "production:line_list"})


# ---------------- Machines ----------------

def machine_list(request):
    machines = Machine.objects.select_related("line")
    return render(request, "production/machine_list.html", {"machines": machines})


def machine_detail(request, pk):
    machine = get_object_or_404(Machine, pk=pk)
    return render(request, "production/machine_detail.html", {"machine": machine})


@login_required
def machine_create(request):
    form = MachineForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Machine added successfully.")
        return redirect("production:machine_list")
    return render(request, "form.html", {"form": form, "title": "Add Machine",
                                         "cancel_url": "production:machine_list"})


@login_required
def machine_update(request, pk):
    machine = get_object_or_404(Machine, pk=pk)
    form = MachineForm(request.POST or None, instance=machine)
    if form.is_valid():
        form.save()
        messages.success(request, "Machine updated successfully.")
        return redirect("production:machine_list")
    return render(request, "form.html", {"form": form, "title": "Edit Machine",
                                         "cancel_url": "production:machine_list"})


@login_required
def machine_delete(request, pk):
    machine = get_object_or_404(Machine, pk=pk)
    if request.method == "POST":
        machine.delete()
        messages.success(request, "Machine deleted successfully.")
        return redirect("production:machine_list")
    return render(request, "confirm_delete.html", {"object": machine,
                                                   "cancel_url": "production:machine_list"})


# ---------------- Workers ----------------

def worker_list(request):
    workers = Worker.objects.select_related("line", "user")
    return render(request, "production/worker_list.html", {"workers": workers})


def worker_detail(request, pk):
    # Shows ONE worker and the orders he/she supervises
    worker = get_object_or_404(Worker, pk=pk)
    orders = worker.supervised_orders.select_related("product")
    return render(request, "production/worker_detail.html", {"worker": worker, "orders": orders})


@login_required
def worker_create(request):
    form = WorkerForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Worker added successfully.")
        return redirect("production:worker_list")
    return render(request, "form.html", {"form": form, "title": "Add Worker",
                                         "cancel_url": "production:worker_list"})


@login_required
def worker_update(request, pk):
    worker = get_object_or_404(Worker, pk=pk)
    form = WorkerForm(request.POST or None, instance=worker)
    if form.is_valid():
        form.save()
        messages.success(request, "Worker updated successfully.")
        return redirect("production:worker_list")
    return render(request, "form.html", {"form": form, "title": "Edit Worker",
                                         "cancel_url": "production:worker_list"})


@login_required
def worker_delete(request, pk):
    worker = get_object_or_404(Worker, pk=pk)
    if request.method == "POST":
        worker.delete()
        messages.success(request, "Worker deleted successfully.")
        return redirect("production:worker_list")
    return render(request, "confirm_delete.html", {"object": worker,
                                                   "cancel_url": "production:worker_list"})


# ---------------- Production orders ----------------

def order_list(request):
    orders = ProductionOrder.objects.select_related("product", "line", "supervisor")
    return render(request, "production/order_list.html", {"orders": orders})


def orders_by_status(request, status):
    # Dynamic URL with a text parameter: /production/orders/status/in_progress/
    status = status.upper()
    valid = dict(ProductionOrder.STATUS_CHOICES)
    if status not in valid:
        raise Http404("Unknown status")
    orders = ProductionOrder.objects.filter(status=status).select_related("product", "line", "supervisor")
    return render(request, "production/order_list.html",
                  {"orders": orders, "status_label": valid[status]})


def order_detail(request, pk):
    order = get_object_or_404(ProductionOrder, pk=pk)
    return render(request, "production/order_detail.html",
                  {"order": order, "requirements": order.material_requirements()})


@login_required
def order_create(request):
    form = ProductionOrderForm(request.POST or None)
    if form.is_valid():
        order = form.save()
        messages.success(request, f"Production order {order.order_no} created successfully.")
        return redirect("production:order_detail", pk=order.pk)
    return render(request, "form.html", {"form": form, "title": "New Production Order",
                                         "cancel_url": "production:order_list"})


@login_required
def order_update(request, pk):
    order = get_object_or_404(ProductionOrder, pk=pk)
    form = ProductionOrderForm(request.POST or None, instance=order)
    if form.is_valid():
        form.save()
        messages.success(request, f"Production order {order.order_no} updated successfully.")
        return redirect("production:order_detail", pk=order.pk)
    return render(request, "form.html", {"form": form, "title": f"Edit Order {order.order_no}",
                                         "cancel_url": "production:order_list"})


@login_required
def order_delete(request, pk):
    order = get_object_or_404(ProductionOrder, pk=pk)
    if request.method == "POST":
        order.delete()
        messages.success(request, "Production order deleted successfully.")
        return redirect("production:order_list")
    return render(request, "confirm_delete.html", {"object": order,
                                                   "cancel_url": "production:order_list"})
