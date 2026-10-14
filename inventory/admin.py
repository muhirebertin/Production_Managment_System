from django.contrib import admin

from .models import BillOfMaterial, Product, RawMaterial


@admin.register(RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "unit", "quantity_in_stock", "reorder_level", "unit_cost")
    search_fields = ("code", "name")


class BillOfMaterialInline(admin.TabularInline):
    model = BillOfMaterial
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "size", "unit_price")
    list_filter = ("category", "size")
    search_fields = ("code", "name")
    inlines = [BillOfMaterialInline]


@admin.register(BillOfMaterial)
class BillOfMaterialAdmin(admin.ModelAdmin):
    list_display = ("product", "material", "quantity_per_unit")
