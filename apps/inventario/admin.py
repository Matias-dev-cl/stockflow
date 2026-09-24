from django.contrib import admin
from .models import Category, Supplier, Product, Location, StockBalance, Movement

admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(Location)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "minimum", "active")
    search_fields = ("sku", "name")
    list_filter = ("category", "active")

@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ("created_at", "kind", "product", "location", "quantity", "user")
    list_filter = ("kind", "location")
    readonly_fields = ("product", "location", "kind", "quantity", "reason", "user", "created_at", "corrects")
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

@admin.register(StockBalance)
class StockBalanceAdmin(admin.ModelAdmin):
    list_display = ("product", "location", "quantity")
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
