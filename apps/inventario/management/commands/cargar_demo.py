from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from apps.inventario.models import Category, Supplier, Product, Location, StockBalance, Movement

class Command(BaseCommand):
    help = "Carga catálogo y saldos de ejemplo para revisión local."
    def handle(self, *args, **options):
        User = get_user_model()
        user, created = User.objects.get_or_create(username="maty", defaults={"email": "maty@example.local", "is_staff": True, "is_superuser": True})
        if created:
            user.set_password("stockflow-demo")
            user.save()
        supplier, _ = Supplier.objects.get_or_create(name="Suministros Andes", defaults={"email": "ventas@example.local"})
        location, _ = Location.objects.get_or_create(code="BOD-01", defaults={"name": "Bodega central"})
        data = [("Tecnología", [("TEC-001", "Teclado inalámbrico", 8, 24), ("TEC-002", "Mouse ergonómico", 12, 7), ("TEC-003", "Monitor 24 pulgadas", 5, 16)]), ("Oficina", [("OFI-010", "Cuaderno ejecutivo", 10, 38), ("OFI-014", "Pack marcadores", 6, 4)])]
        for category_name, entries in data:
            category, _ = Category.objects.get_or_create(name=category_name)
            for sku, name, minimum, quantity in entries:
                product, _ = Product.objects.get_or_create(sku=sku, defaults={"name": name, "category": category, "supplier": supplier, "minimum": minimum})
                balance, created = StockBalance.objects.get_or_create(product=product, location=location, defaults={"quantity": quantity})
                if created:
                    Movement.objects.create(product=product, location=location, kind=Movement.Kind.IN, quantity=quantity, reason="Stock inicial de demostración", user=user)
        self.stdout.write(self.style.SUCCESS("Demo cargada. Usuario: maty · contraseña: stockflow-demo"))
