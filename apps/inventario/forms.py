from django import forms
from .models import Product, Location, Movement

class MovementForm(forms.Form):
    kind = forms.ChoiceField(label="Tipo de movimiento", choices=Movement.Kind.choices)
    product = forms.ModelChoiceField(label="Producto", queryset=Product.objects.filter(active=True))
    location = forms.ModelChoiceField(label="Ubicación", queryset=Location.objects.filter(active=True))
    quantity = forms.IntegerField(label="Cantidad / delta de ajuste")
    reason = forms.CharField(label="Motivo", max_length=240, widget=forms.TextInput(attrs={"placeholder": "Ej. Reposición de compra #1048"}))

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

class QuickProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "minimum"]
        labels = {"name": "Nombre", "minimum": "Stock mínimo"}
        widgets = {"name": forms.TextInput(attrs={"placeholder": "Nombre del producto"}), "minimum": forms.NumberInput(attrs={"min": 0})}

class QuickMovementForm(forms.Form):
    kind = forms.ChoiceField(label="Acción", choices=Movement.Kind.choices)
    location = forms.ModelChoiceField(label="Ubicación", queryset=Location.objects.filter(active=True))
    quantity = forms.IntegerField(label="Cantidad o delta de ajuste")
    reason = forms.CharField(label="Motivo", max_length=240, widget=forms.TextInput(attrs={"placeholder": "Ej. Reposición o entrega"}))

    def clean(self):
        data = super().clean()
        quantity, kind = data.get("quantity"), data.get("kind")
        if quantity is not None and kind in ("IN", "OUT") and quantity < 1:
            self.add_error("quantity", "Usa una cantidad mayor que cero.")
        if quantity == 0 and kind == "ADJUST":
            self.add_error("quantity", "El ajuste debe ser distinto de cero.")
        return data
