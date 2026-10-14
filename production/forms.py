import re

from django import forms

from inventory.forms import StyledModelForm
from .models import Machine, ProductionLine, ProductionOrder, Worker


class ProductionLineForm(StyledModelForm):
    class Meta:
        model = ProductionLine
        fields = ["name", "location", "daily_capacity"]


class MachineForm(StyledModelForm):
    class Meta:
        model = Machine
        fields = ["code", "name", "machine_type", "line", "status"]

    def clean_code(self):
        # Validation: machine code like SEW-01 (letters, dash, 2 digits)
        code = self.cleaned_data["code"].strip().upper()
        if not re.fullmatch(r"[A-Z]{3}-\d{2}", code):
            raise forms.ValidationError("Use the format SEW-01.")
        return code


class WorkerForm(StyledModelForm):
    class Meta:
        model = Worker
        fields = ["employee_no", "first_name", "last_name", "role", "phone", "line"]

    def clean_employee_no(self):
        # Validation: employee number like EMP001
        number = self.cleaned_data["employee_no"].strip().upper()
        if not re.fullmatch(r"EMP\d{3}", number):
            raise forms.ValidationError("Use the format EMP001.")
        return number

    def clean_phone(self):
        # Validation: Rwandan mobile number, 10 digits starting with 07
        phone = self.cleaned_data["phone"].replace(" ", "")
        if not re.fullmatch(r"07\d{8}", phone):
            raise forms.ValidationError("Enter a 10-digit number starting with 07, e.g. 0788123456.")
        return phone


class ProductionOrderForm(StyledModelForm):
    class Meta:
        model = ProductionOrder
        fields = ["order_no", "product", "line", "supervisor", "quantity",
                  "quantity_produced", "start_date", "due_date", "status"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "due_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only supervisors can lead an order
        self.fields["supervisor"].queryset = Worker.objects.filter(role="SUPERVISOR")

    def clean_order_no(self):
        # Validation: order number like PO-2026-001
        number = self.cleaned_data["order_no"].strip().upper()
        if not re.fullmatch(r"PO-\d{4}-\d{3}", number):
            raise forms.ValidationError("Use the format PO-2026-001.")
        return number

    def clean(self):
        # Validation across several fields
        cleaned = super().clean()
        start, due = cleaned.get("start_date"), cleaned.get("due_date")
        quantity, produced = cleaned.get("quantity"), cleaned.get("quantity_produced")
        status, line, supervisor = cleaned.get("status"), cleaned.get("line"), cleaned.get("supervisor")
        product = cleaned.get("product")

        if start and due and due < start:
            self.add_error("due_date", "Due date cannot be before the start date.")
        if quantity and produced is not None and produced > quantity:
            self.add_error("quantity_produced", "Produced cannot be more than the quantity ordered.")
        if status == "COMPLETED" and quantity and produced != quantity:
            self.add_error("status", "An order can only be completed when all units are produced.")
        if supervisor and line and supervisor.line != line:
            self.add_error("supervisor", "This supervisor works on another production line.")

        # Business rule: a NEW order needs enough raw materials in stock
        if not self.instance.pk and product and quantity:
            shortages = []
            for item in product.bom_items.select_related("material"):
                needed = item.quantity_per_unit * quantity
                if item.material.quantity_in_stock < needed:
                    shortages.append(f"{item.material.name}: need {needed.normalize():f} {item.material.unit}, "
                                     f"only {item.material.quantity_in_stock.normalize():f} in stock")
            if shortages:
                raise forms.ValidationError(["Not enough raw materials:"] + shortages)
        return cleaned
