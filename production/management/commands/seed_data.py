"""Fill the database with a small set of sample data:  python manage.py seed_data

Sample factory: Inzozi Garments Ltd, Kigali Special Economic Zone (Masoro), Gasabo.
It makes school uniforms, kitenge dresses and corporate polo shirts.
"""
from datetime import date

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from inventory.models import BillOfMaterial, Product, RawMaterial
from production.models import Machine, ProductionLine, ProductionOrder, Worker


class Command(BaseCommand):
    help = "Create sample materials, products, lines, machines, workers and orders."

    def handle(self, *args, **options):
        # Raw materials: code, name, unit, stock, reorder level, unit cost (RWF)
        materials = {}
        for code, name, unit, stock, reorder, cost in [
            ("RM-001", "Blue poplin fabric", "m", 450, 200, 2800),
            ("RM-002", "Khaki drill fabric", "m", 160, 200, 3200),
            ("RM-003", "Kitenge wax print fabric", "m", 120, 60, 5500),
            ("RM-004", "Pique knit fabric", "m", 300, 100, 4000),
            ("RM-005", "Polyester sewing thread", "cone", 30, 15, 1500),
            ("RM-006", "Plastic buttons", "pcs", 2000, 600, 20),
        ]:
            materials[code] = RawMaterial.objects.get_or_create(code=code, defaults={
                "name": name, "unit": unit, "quantity_in_stock": stock,
                "reorder_level": reorder, "unit_cost": cost})[0]

        # Products: code, name, category, size, unit price (RWF)
        products = {}
        for code, name, category, size, price in [
            ("GR-101", "School uniform shirt", "UNIFORM", "M", 4500),
            ("GR-102", "School uniform trousers", "UNIFORM", "M", 6000),
            ("GR-201", "Kitenge dress", "DRESS", "M", 18000),
            ("GR-301", "Corporate polo shirt", "SHIRT", "L", 8500),
        ]:
            products[code] = Product.objects.get_or_create(code=code, defaults={
                "name": name, "category": category, "size": size, "unit_price": price})[0]

        # Bill of materials: how much of each material ONE garment needs
        for product, material, qty in [
            ("GR-101", "RM-001", 1.3), ("GR-101", "RM-005", 0.04), ("GR-101", "RM-006", 7),
            ("GR-102", "RM-002", 1.1), ("GR-102", "RM-005", 0.04), ("GR-102", "RM-006", 1),
            ("GR-201", "RM-003", 3.0), ("GR-201", "RM-005", 0.05),
            ("GR-301", "RM-004", 1.2), ("GR-301", "RM-005", 0.03), ("GR-301", "RM-006", 3),
        ]:
            BillOfMaterial.objects.get_or_create(product=products[product], material=materials[material],
                                                 defaults={"quantity_per_unit": qty})

        # Production lines
        line_a = ProductionLine.objects.get_or_create(name="Line A - School Uniforms", defaults={
            "location": "KSEZ Masoro, Hall 1", "daily_capacity": 150})[0]
        line_b = ProductionLine.objects.get_or_create(name="Line B - Kitenge & Corporate Wear", defaults={
            "location": "KSEZ Masoro, Hall 2", "daily_capacity": 60})[0]

        # Machines
        for code, name, mtype, line, status in [
            ("CUT-01", "Straight knife cutting machine", "CUTTING", line_a, "ACTIVE"),
            ("SEW-01", "Juki lockstitch sewing machine", "SEWING", line_a, "ACTIVE"),
            ("SEW-02", "Juki lockstitch sewing machine", "SEWING", line_b, "ACTIVE"),
            ("OVL-01", "Overlock machine", "OVERLOCK", line_b, "MAINTENANCE"),
        ]:
            Machine.objects.get_or_create(code=code, defaults={
                "name": name, "machine_type": mtype, "line": line, "status": status})

        # Workers
        workers = {}
        for no, first, last, role, phone, line in [
            ("EMP001", "Jean Paul", "Mugabo", "SUPERVISOR", "0788123456", line_a),
            ("EMP002", "Diane", "Uwase", "OPERATOR", "0722345678", line_a),
            ("EMP003", "Eric", "Habimana", "SUPERVISOR", "0783456789", line_b),
            ("EMP004", "Aline", "Mukamana", "QC", "0735678901", line_b),
        ]:
            workers[no] = Worker.objects.get_or_create(employee_no=no, defaults={
                "first_name": first, "last_name": last, "role": role, "phone": phone, "line": line})[0]

        # Production orders
        for no, product, line, sup, qty, done, start, due, status in [
            ("PO-2026-001", "GR-101", line_a, "EMP001", 600, 600, date(2026, 9, 14), date(2026, 9, 25), "COMPLETED"),
            ("PO-2026-002", "GR-102", line_a, "EMP001", 400, 220, date(2026, 10, 1), date(2026, 10, 10), "IN_PROGRESS"),
            ("PO-2026-003", "GR-201", line_b, "EMP003", 30, 12, date(2026, 10, 6), date(2026, 10, 16), "IN_PROGRESS"),
            ("PO-2026-004", "GR-301", line_b, "EMP003", 100, 0, date(2026, 10, 19), date(2026, 10, 30), "PLANNED"),
            ("PO-2026-005", "GR-101", line_a, "EMP001", 300, 0, date(2026, 11, 2), date(2026, 11, 13), "PLANNED"),
        ]:
            ProductionOrder.objects.get_or_create(order_no=no, defaults={
                "product": products[product], "line": line, "supervisor": workers[sup], "quantity": qty,
                "quantity_produced": done, "start_date": start, "due_date": due, "status": status})

        # Users: one superuser (admin) and one supervisor login (OneToOne link)
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@inzozigarments.rw", "Admin@2026")
        if not User.objects.filter(username="jmugabo").exists():
            user = User.objects.create_user("jmugabo", "jmugabo@inzozigarments.rw", "Supervisor@2026")
            supervisor = workers["EMP001"]
            supervisor.user = user
            supervisor.save()

        self.stdout.write(self.style.SUCCESS(
            f"Done: {RawMaterial.objects.count()} materials, {Product.objects.count()} products, "
            f"{ProductionLine.objects.count()} lines, {Machine.objects.count()} machines, "
            f"{Worker.objects.count()} workers, {ProductionOrder.objects.count()} orders."))
