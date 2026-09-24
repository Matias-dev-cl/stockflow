from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

class Category(models.Model):
    name = models.CharField("nombre", max_length=80, unique=True)
    class Meta: ordering = ["name"]
    def __str__(self): return self.name

class Supplier(models.Model):
    name = models.CharField("proveedor", max_length=140)
    email = models.EmailField(blank=True)
    active = models.BooleanField(default=True)
    class Meta: ordering = ["name"]
    def __str__(self): return self.name

class Product(models.Model):
    sku = models.CharField("SKU", max_length=32, unique=True)
    name = models.CharField("producto", max_length=160)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="products", null=True, blank=True)
    unit = models.CharField(max_length=24, default="unidad")
    minimum = models.PositiveIntegerField("stock mínimo", default=5)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["name"]
    def __str__(self): return f"{self.sku} · {self.name}"
    @property
    def stock(self): return sum(b.quantity for b in self.balances.all())

class Location(models.Model):
    code = models.CharField(max_length=24, unique=True)
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    class Meta: ordering = ["name"]
    def __str__(self): return self.name

class StockBalance(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="balances")
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="balances")
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    class Meta:
        constraints = [models.UniqueConstraint(fields=["product", "location"], name="unique_product_location_balance"), models.CheckConstraint(condition=models.Q(quantity__gte=0), name="stock_balance_nonnegative")]
    def __str__(self): return f"{self.product} / {self.location}: {self.quantity}"

class Movement(models.Model):
    class Kind(models.TextChoices):
        IN = "IN", "Entrada"
        OUT = "OUT", "Salida"
        ADJUST = "ADJUST", "Ajuste"
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="movements")
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="movements")
    kind = models.CharField(max_length=8, choices=Kind.choices)
    quantity = models.IntegerField()
    reason = models.CharField("motivo", max_length=240)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stock_movements")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    corrects = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="corrections")
    class Meta: ordering = ["-created_at", "-pk"]
    def __str__(self): return f"{self.get_kind_display()} · {self.product} · {self.quantity}"
