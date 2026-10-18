from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Movement, Product, Location, StockBalance

@transaction.atomic
def record_movement(*, product: Product, location: Location, kind: str, quantity: int, reason: str, user, corrects=None):
    if not user or not user.is_authenticated or not user.is_active:
        raise ValidationError("Se requiere un usuario activo para registrar movimientos.")
    if not product.active or not location.active:
        raise ValidationError("El producto y la ubicación deben estar activos.")
    if kind not in Movement.Kind.values:
        raise ValidationError("Tipo de movimiento no válido.")
    if type(quantity) is not int or (kind in (Movement.Kind.IN, Movement.Kind.OUT) and quantity < 1) or (kind == Movement.Kind.ADJUST and quantity == 0):
        raise ValidationError("La cantidad debe ser positiva; un ajuste requiere un delta distinto de cero.")
    reason = reason.strip() if isinstance(reason, str) else ""
    if not reason or len(reason) > 240:
        raise ValidationError("Escribe un motivo de entre 1 y 240 caracteres.")
    if not -(2**31) <= quantity <= 2**31 - 1:
        raise ValidationError("La cantidad excede el límite admitido.")
    balance, _ = StockBalance.objects.get_or_create(product=product, location=location)
    balance = StockBalance.objects.select_for_update().get(pk=balance.pk)
    change = quantity if kind in (Movement.Kind.IN, Movement.Kind.ADJUST) else -quantity
    if balance.quantity + change < 0:
        raise ValidationError(f"Stock insuficiente: hay {balance.quantity} {product.unit} disponibles en {location.name}.")
    if balance.quantity + change > 2**31 - 1:
        raise ValidationError("El saldo resultante excede el límite admitido.")
    movement = Movement.objects.create(product=product, location=location, kind=kind, quantity=quantity, reason=reason, user=user, corrects=corrects)
    balance.quantity += change
    balance.save(update_fields=["quantity"])
    return movement, balance
