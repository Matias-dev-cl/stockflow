from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import F, Q, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import MovementForm, ProductForm, QuickMovementForm, QuickProductForm
from .models import Movement, Product, StockBalance
from .services import record_movement


def require_catalog_manager(user):
    if not user.is_staff:
        raise PermissionDenied("Solo administración puede modificar el catálogo.")


@login_required
@require_GET
def dashboard(request):
    products = Product.objects.filter(active=True).select_related("category").prefetch_related("balances")
    amounts = dict(
        StockBalance.objects.filter(product__active=True)
        .values("product_id").annotate(total=Sum("quantity")).values_list("product_id", "total")
    )
    low = [p for p in products if p.minimum > 0 and amounts.get(p.id, 0) <= p.minimum]
    context = {
        "total_products": len(products), "total_stock": sum(amounts.values()),
        "low_stock": len(low), "total_movements": Movement.objects.count(),
        "low_products": low[:5],
        "movements": Movement.objects.select_related("product__category", "location", "user")[:8],
    }
    return render(request, "inventario/dashboard.html", context)


@login_required
@require_GET
def product_list(request):
    query = request.GET.get("q", "").strip()
    state = request.GET.get("estado", "activos")
    if state not in ("activos", "reponer", "archivados"):
        state = "activos"
    products = Product.objects.filter(active=state != "archivados").select_related(
        "category", "supplier"
    ).prefetch_related("balances")
    if state == "reponer":
        products = products.annotate(stock_total=Coalesce(Sum("balances__quantity"), 0)).filter(
            minimum__gt=0, stock_total__lte=F("minimum")
        )
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(sku__icontains=query) | Q(category__name__icontains=query)
        )
    page = Paginator(products.order_by("name", "pk"), 20).get_page(request.GET.get("page"))
    return render(request, "inventario/products.html", {
        "products": page, "page_obj": page, "query": query, "state": state,
    })


@login_required
@require_http_methods(["GET", "POST"])
def product_create(request):
    require_catalog_manager(request.user)
    form = ProductForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        product = form.save()
        messages.success(request, f"Producto {product.sku} creado. Ahora puedes registrar su stock inicial.")
        return redirect("product_detail", pk=product.pk)
    return render(request, "inventario/product_form.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def product_update(request, pk):
    require_catalog_manager(request.user)
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST if request.method == "POST" else None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Datos del producto actualizados.")
        return redirect("product_detail", pk=product.pk)
    return render(request, "inventario/product_form.html", {"form": form, "product": product})


@login_required
@require_POST
def product_status(request, pk):
    require_catalog_manager(request.user)
    product = get_object_or_404(Product, pk=pk)
    action = request.POST.get("action")
    if action not in ("archive", "restore"):
        return HttpResponseBadRequest("Acción no válida.")
    product.active = action == "restore"
    product.save(update_fields=["active"])
    messages.success(request, "Producto reactivado." if product.active else "Producto archivado. Su historial sigue disponible.")
    return redirect("product_detail", pk=product.pk)


@login_required
@require_http_methods(["GET", "POST"])
def movements(request):
    form = MovementForm(
        request.POST if request.method == "POST" else None,
        initial={"product": request.GET.get("producto"), "kind": request.GET.get("tipo", "IN")},
    )
    if request.method == "POST" and form.is_valid():
        try:
            movement, balance = record_movement(user=request.user, **form.cleaned_data)
            messages.success(request, f"Movimiento registrado. Nuevo saldo: {balance.quantity} {movement.product.unit}.")
            return redirect("movements")
        except ValidationError as exc:
            form.add_error(None, exc.messages[0])
    rows = Movement.objects.select_related("product", "location", "user")
    page = Paginator(rows, 20).get_page(request.GET.get("page"))
    return render(request, "inventario/movements.html", {"form": form, "movements": page, "page_obj": page})


@login_required
@require_http_methods(["GET", "POST"])
def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.select_related("category", "supplier").prefetch_related("balances__location"), pk=pk
    )
    action = request.POST.get("action") if request.method == "POST" else None
    if action == "quick_edit":
        require_catalog_manager(request.user)
    quick_edit_form = QuickProductForm(
        request.POST if action == "quick_edit" else None, instance=product
    )
    balances = list(product.balances.all())
    initial_location = next((b.location_id for b in balances if b.location.active), None)
    quick_movement_form = QuickMovementForm(
        request.POST if action == "quick_stock" else None,
        initial={"location": initial_location, "kind": "IN"},
    )
    if action == "quick_edit" and quick_edit_form.is_valid():
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
    page = Paginator(product.movements.select_related("location", "user"), 10).get_page(request.GET.get("page"))
    return render(request, "inventario/product_detail.html", {
        "product": product, "movements": page, "page_obj": page,
        "quick_edit_form": quick_edit_form, "quick_movement_form": quick_movement_form,
    })


@login_required
@require_GET
def replenishment(request):
    products = Product.objects.filter(active=True).select_related("category", "supplier").prefetch_related("balances__location")
    items = []
    for product in products:
        total = product.stock
        if product.minimum > 0 and total <= product.minimum:
            items.append({"product": product, "total": total})
    return render(request, "inventario/replenishment.html", {"items": items})


@login_required
@require_GET
def guide(request):
    return render(request, "inventario/guide.html")
