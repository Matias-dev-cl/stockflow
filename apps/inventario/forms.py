from django import forms
from django.db.models import Q
from .models import Product, Location, Movement

class MovementForm(forms.Form):
    kind = forms.ChoiceField(label="Tipo de movimiento", choices=Movement.Kind.choices)
    product = forms.ModelChoiceField(label="Producto", queryset=Product.objects.filter(active=True))
    location = forms.ModelChoiceField(label="Ubicación", queryset=Location.objects.filter(active=True))
    quantity = forms.IntegerField(label="Cantidad", help_text="Entrada o salida: cantidad positiva. Ajuste: diferencia con signo, por ejemplo -3 si contaste tres unidades menos.")
    reason = forms.CharField(label="Motivo", max_length=240, widget=forms.TextInput(attrs={"placeholder": "Ej. Reposición de compra #1048"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].empty_label = "Selecciona un producto"
        self.fields["location"].empty_label = "Selecciona una ubicación"

    def clean(self):
        data = super().clean()
        quantity, kind = data.get("quantity"), data.get("kind")
        if quantity is not None and kind in ("IN", "OUT") and quantity < 1:
            self.add_error("quantity", "La cantidad debe ser mayor que cero.")
        if quantity == 0 and kind == "ADJUST":
            self.add_error("quantity", "El delta debe ser distinto de cero.")
        return data

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["sku", "name", "category", "supplier", "unit", "minimum"]
        labels = {"category": "Categoría", "supplier": "Proveedor", "unit": "Unidad"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].empty_label = "Selecciona una categoría"
        self.fields["supplier"].empty_label = "Sin proveedor"
        self.fields["supplier"].queryset = self.fields["supplier"].queryset.filter(
            Q(active=True) | Q(pk=self.instance.supplier_id)
        )
        if self.instance.pk and self.instance.movements.exists():
            self.fields["unit"].widget.attrs["readonly"] = True
            self.fields["unit"].help_text = "La unidad se conserva porque este producto ya tiene movimientos."

class QuickProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "minimum"]
        labels = {"name": "Nombre", "minimum": "Stock mínimo"}
        widgets = {"name": forms.TextInput(attrs={"placeholder": "Nombre del producto"}), "minimum": forms.NumberInput(attrs={"min": 0})}

class QuickMovementForm(forms.Form):
    kind = forms.ChoiceField(label="Acción", choices=Movement.Kind.choices)
    location = forms.ModelChoiceField(label="Ubicación", queryset=Location.objects.filter(active=True))
    quantity = forms.IntegerField(label="Cantidad", help_text="Para corregir un conteo usa una diferencia con signo: +3 o -3. Las entradas y salidas requieren cantidades positivas.")
    reason = forms.CharField(label="Motivo", max_length=240, widget=forms.TextInput(attrs={"placeholder": "Ej. Reposición o entrega"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["location"].empty_label = "Selecciona una ubicación"

    def clean(self):
        data = super().clean()
        quantity, kind = data.get("quantity"), data.get("kind")
        if quantity is not None and kind in ("IN", "OUT") and quantity < 1:
            self.add_error("quantity", "Usa una cantidad mayor que cero.")
        if quantity == 0 and kind == "ADJUST":
            self.add_error("quantity", "El ajuste debe ser distinto de cero.")
        return data
