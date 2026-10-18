from rest_framework import serializers
from .models import Product, Movement

class ProductSerializer(serializers.ModelSerializer):
    stock = serializers.IntegerField(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    class Meta:
        model = Product
        fields = ["id", "sku", "name", "category", "category_name", "unit", "minimum", "stock", "active"]

class MovementSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(active=True))
    delta = serializers.IntegerField(read_only=True)
    class Meta:
        model = Movement
        fields = ["id", "product", "location", "kind", "quantity", "delta", "reason", "user", "created_at"]
        read_only_fields = ["id", "user", "created_at"]
