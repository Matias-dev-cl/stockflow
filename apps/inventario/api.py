from rest_framework import generics, permissions, serializers
from rest_framework.exceptions import ValidationError
from .models import Product, Movement
from .serializers import ProductSerializer, MovementSerializer
from .services import record_movement

class ProductListAPI(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Product.objects.filter(active=True).select_related("category").prefetch_related("balances")

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
        except Exception as exc:
            from django.core.exceptions import ValidationError as DjangoValidationError
            if isinstance(exc, DjangoValidationError): raise ValidationError(exc.messages)
            raise
        return Response(self.get_serializer(movement).data, status=201)

from rest_framework.response import Response
