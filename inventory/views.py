from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BillOfMaterialForm, ProductForm, RawMaterialForm
from .models import BillOfMaterial, Product, RawMaterial


# ---------------- Raw materials ----------------

def material_list(request):
    materials = RawMaterial.objects.all()
    return render(request, "inventory/material_list.html", {"materials": materials})


def material_detail(request, pk):
    # Shows ONE material and the products that use it (through the bill of materials)
    material = get_object_or_404(RawMaterial, pk=pk)
    bom_items = material.bom_items.select_related("product")
    return render(request, "inventory/material_detail.html",
                  {"material": material, "bom_items": bom_items})


@login_required
def material_create(request):
    form = RawMaterialForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Raw material added successfully.")
        return redirect("inventory:material_list")
    return render(request, "form.html", {"form": form, "title": "Add Raw Material",
                                         "cancel_url": "inventory:material_list"})


@login_required
def material_update(request, pk):
    material = get_object_or_404(RawMaterial, pk=pk)
    form = RawMaterialForm(request.POST or None, instance=material)
    if form.is_valid():
        form.save()
        messages.success(request, "Raw material updated successfully.")
        return redirect("inventory:material_list")
    return render(request, "form.html", {"form": form, "title": "Edit Raw Material",
                                         "cancel_url": "inventory:material_list"})


@login_required
def material_delete(request, pk):
    material = get_object_or_404(RawMaterial, pk=pk)
    if request.method == "POST":  # user clicked "Yes, delete" on the confirmation page
        try:
            material.delete()
            messages.success(request, "Raw material deleted successfully.")
        except ProtectedError:
            messages.error(request, "Cannot delete: this material is used in a product's bill of materials.")
        return redirect("inventory:material_list")
    return render(request, "confirm_delete.html", {"object": material,
                                                   "cancel_url": "inventory:material_list"})


# ---------------- Products ----------------

def product_list(request):
    products = Product.objects.prefetch_related("bom_items")
    return render(request, "inventory/product_list.html", {"products": products})


def product_detail(request, pk):
    # Dynamic URL: /inventory/products/<pk>/ shows ONE product and its bill of materials
    product = get_object_or_404(Product, pk=pk)
    bom_items = product.bom_items.select_related("material")
    orders = product.orders.select_related("line")
    return render(request, "inventory/product_detail.html",
                  {"product": product, "bom_items": bom_items, "orders": orders})


@login_required
def product_create(request):
    form = ProductForm(request.POST or None)
    if form.is_valid():
        product = form.save()
        messages.success(request, f"Product {product.code} added. Now add its materials.")
        return redirect("inventory:product_detail", pk=product.pk)
    return render(request, "form.html", {"form": form, "title": "Add Product",
                                         "cancel_url": "inventory:product_list"})


@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        messages.success(request, f"Product {product.code} updated successfully.")
        return redirect("inventory:product_detail", pk=product.pk)
    return render(request, "form.html", {"form": form, "title": "Edit Product",
                                         "cancel_url": "inventory:product_list"})


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        try:
            product.delete()
            messages.success(request, "Product deleted successfully.")
        except ProtectedError:
            messages.error(request, "Cannot delete: this product has production orders.")
        return redirect("inventory:product_list")
    return render(request, "confirm_delete.html", {"object": product,
                                                   "cancel_url": "inventory:product_list"})


# ---------------- Bill of materials (ManyToMany "through" model) ----------------

@login_required
def bom_add(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    form = BillOfMaterialForm(request.POST or None, product=product)
    if form.is_valid():
        item = form.save(commit=False)   # do not save yet ...
        item.product = product           # ... first link it to the product from the URL
        item.save()
        messages.success(request, f"{item.material.name} added to {product.code}.")
        return redirect("inventory:product_detail", pk=product.pk)
    return render(request, "form.html", {"form": form, "title": f"Add Material to {product.code}",
                                         "cancel_url": "inventory:product_list"})


@login_required
def bom_delete(request, pk):
    item = get_object_or_404(BillOfMaterial, pk=pk)
    product_pk = item.product.pk
    if request.method == "POST":
        item.delete()
        messages.success(request, "Material removed from the bill of materials.")
        return redirect("inventory:product_detail", pk=product_pk)
    return render(request, "confirm_delete.html", {"object": item,
                                                   "cancel_url": "inventory:product_list"})
