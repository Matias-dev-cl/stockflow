from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import filters, generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .models import Product, Movement
from .serializers import ProductSerializer, MovementSerializer
from .services import record_movement

class ProductListAPI(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Product.objects.filter(active=True).select_related("category").prefetch_related("balances")
    filter_backends = [filters.SearchFilter]
    search_fields = ["sku", "name", "category__name"]

class MovementListCreateAPI(generics.ListCreateAPIView):
    serializer_class = MovementSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Movement.objects.select_related("product", "location", "user")
    def create(self, request, *args, **kwargs):
        incoming = self.get_serializer(data=request.data)
        incoming.is_valid(raise_exception=True)
        data = incoming.validated_data
        try:
            movement, _ = record_movement(user=request.user, **data)
        except DjangoValidationError as exc:
            raise ValidationError({"detail": exc.messages}) from exc
        return Response(self.get_serializer(movement).data, status=status.HTTP_201_CREATED)
