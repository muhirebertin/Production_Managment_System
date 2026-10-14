from django.core.validators import MinValueValidator
from django.db import models


class RawMaterial(models.Model):
    """Materials used to make garments: fabric, thread, buttons, zippers..."""
    UNIT_CHOICES = [("m", "Metres"), ("pcs", "Pieces"), ("cone", "Cones"), ("kg", "Kilograms")]

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=4, choices=UNIT_CHOICES)
    quantity_in_stock = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    reorder_level = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
        help_text="Warn when stock falls to this level.")
    unit_cost = models.DecimalField(
        "Unit cost (RWF)", max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def is_low_stock(self):
        return self.quantity_in_stock <= self.reorder_level


class Product(models.Model):
    """A garment the factory makes. Its materials are listed in the bill of materials."""
    CATEGORY_CHOICES = [("SHIRT", "Shirt"), ("TROUSERS", "Trousers"),
                        ("UNIFORM", "Uniform"), ("DRESS", "Dress")]
    SIZE_CHOICES = [("S", "Small"), ("M", "Medium"), ("L", "Large"), ("XL", "Extra large")]

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    size = models.CharField(max_length=2, choices=SIZE_CHOICES)
    unit_price = models.DecimalField(
        "Unit price (RWF)", max_digits=10, decimal_places=2, validators=[MinValueValidator(1)])
    # Many-to-many: a product uses many materials, a material is used in many products.
    # The extra data (quantity per unit) is stored in BillOfMaterial ("through").
    materials = models.ManyToManyField(RawMaterial, through="BillOfMaterial",
                                       related_name="products", blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name} ({self.size})"


class BillOfMaterial(models.Model):
    """How much of ONE material is needed to make ONE unit of a product."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="bom_items")
    material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT, related_name="bom_items")
    quantity_per_unit = models.DecimalField(
        max_digits=8, decimal_places=3, validators=[MinValueValidator(0.001)])

    class Meta:
        ordering = ["material__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "material"], name="unique_product_material",
                violation_error_message="This material is already in the product's bill of materials.",
            )
        ]

    def __str__(self):
        return f"{self.product.code}: {self.quantity_per_unit} {self.material.unit} of {self.material.name}"

    @property
    def cost_per_unit(self):
        """Cost of this material in ONE garment (quantity x unit cost)."""
        return self.quantity_per_unit * self.material.unit_cost
