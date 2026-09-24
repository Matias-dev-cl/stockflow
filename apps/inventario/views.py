from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import MovementForm, ProductForm, QuickMovementForm, QuickProductForm
from .models import Product, Movement, StockBalance
from .services import record_movement

@login_required
def dashboard(request):
    products = Product.objects.filter(active=True).select_related("category").prefetch_related("balances")
    balances = StockBalance.objects.filter(product__active=True).values("product_id").annotate(total=Sum("quantity"))
    amounts = {row["product_id"]: row["total"] for row in balances}
    low = [p for p in products if p.minimum > 0 and amounts.get(p.id, 0) <= p.minimum]
    context = {"total_products": products.count(), "total_stock": sum(amounts.values()), "low_stock": len(low), "total_movements": Movement.objects.count(), "low_products": low[:5], "movements": Movement.objects.select_related("product", "location", "user")[:8]}
    return render(request, "inventario/dashboard.html", context)

@login_required
def product_list(request):
    query = request.GET.get("q", "").strip()
    products = Product.objects.filter(active=True).select_related("category", "supplier").prefetch_related("balances")
    if query: products = products.filter(Q(name__icontains=query) | Q(sku__icontains=query) | Q(category__name__icontains=query))
    return render(request, "inventario/products.html", {"products": products, "query": query})

@login_required
def product_create(request):
    if not request.user.is_staff:
        messages.error(request, "Solo administración puede modificar el catálogo."); return redirect("products")
    form = ProductForm(request.POST or None)
    if form.is_valid():
        product = form.save(); messages.success(request, f"Producto {product.sku} creado."); return redirect("products")
    return render(request, "inventario/product_form.html", {"form": form})

@login_required
def movements(request):
    form = MovementForm(request.POST or None, initial={"product": request.GET.get("producto"), "kind": request.GET.get("tipo", "IN")})
    if request.method == "POST" and form.is_valid():
        try:
            movement, balance = record_movement(user=request.user, **form.cleaned_data)
            messages.success(request, f"Movimiento registrado. Nuevo saldo: {balance.quantity} {movement.product.unit}.")
            return redirect("movements")
        except ValidationError as exc:
            form.add_error(None, exc.messages[0])
    rows = Movement.objects.select_related("product", "location", "user")[:30]
    return render(request, "inventario/movements.html", {"form": form, "movements": rows})

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related("category", "supplier").prefetch_related("balances__location"), pk=pk, active=True)
    action = request.POST.get("action") if request.method == "POST" else None
    quick_edit_form = QuickProductForm(request.POST if action == "quick_edit" else None, instance=product)
    initial_location = product.balances.first().location_id if product.balances.exists() else None
    quick_movement_form = QuickMovementForm(request.POST if action == "quick_stock" else None, initial={"location": initial_location, "kind": "IN"})
    if action == "quick_edit" and quick_edit_form.is_valid():
        if not request.user.is_staff:
            messages.error(request, "Solo administración puede editar el producto.")
        else:
            quick_edit_form.save()
            messages.success(request, "Cambios del producto guardados.")
            return redirect("product_detail", pk=product.pk)
    if action == "quick_stock" and quick_movement_form.is_valid():
        try:
            movement, balance = record_movement(product=product, user=request.user, **quick_movement_form.cleaned_data)
            messages.success(request, f"Listo: nuevo stock de {balance.quantity} {product.unit} en {movement.location.name}.")
            return redirect("product_detail", pk=product.pk)
        except ValidationError as exc:
            quick_movement_form.add_error(None, exc.messages[0])
    return render(request, "inventario/product_detail.html", {"product": product, "movements": product.movements.select_related("location", "user")[:20], "quick_edit_form": quick_edit_form, "quick_movement_form": quick_movement_form})

@login_required
def replenishment(request):
    products = Product.objects.filter(active=True).select_related("category").prefetch_related("balances__location")
    items = []
    for p in products:
        total = sum(b.quantity for b in p.balances.all())
        if p.minimum > 0 and total <= p.minimum: items.append({"product": p, "total": total})
    return render(request, "inventario/replenishment.html", {"items": items})
