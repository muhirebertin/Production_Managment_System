import re

from django import forms

from .models import BillOfMaterial, Product, RawMaterial


class StyledModelForm(forms.ModelForm):
    """Adds the Bootstrap 'form-control' class to every field (AdminLTE style)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class RawMaterialForm(StyledModelForm):
    class Meta:
        model = RawMaterial
        fields = ["code", "name", "unit", "quantity_in_stock", "reorder_level", "unit_cost"]

    def clean_code(self):
        # Validation: material code must look like RM-001
        code = self.cleaned_data["code"].strip().upper()
        if not re.fullmatch(r"RM-\d{3}", code):
            raise forms.ValidationError("Use the format RM-001.")
        return code


class ProductForm(StyledModelForm):
    class Meta:
        model = Product
        fields = ["code", "name", "category", "size", "unit_price"]

    def clean_code(self):
        # Validation: product code must look like GR-101
        code = self.cleaned_data["code"].strip().upper()
        if not re.fullmatch(r"GR-\d{3}", code):
            raise forms.ValidationError("Use the format GR-101.")
        return code


class BillOfMaterialForm(StyledModelForm):
    """Adds one material line to a product. The product comes from the URL."""

    class Meta:
        model = BillOfMaterial
        fields = ["material", "quantity_per_unit"]

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product

    def clean_material(self):
        # Validation: the same material cannot be added twice to one product
        material = self.cleaned_data["material"]
        if BillOfMaterial.objects.filter(product=self.product, material=material).exists():
            raise forms.ValidationError("This material is already in the bill of materials.")
        return material
