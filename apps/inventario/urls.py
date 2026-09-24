from django.urls import path
from . import views
from .api import ProductListAPI, MovementListCreateAPI

urlpatterns = [path("", views.dashboard, name="dashboard"), path("productos/", views.product_list, name="products"), path("productos/nuevo/", views.product_create, name="product_create"), path("productos/<int:pk>/", views.product_detail, name="product_detail"), path("movimientos/", views.movements, name="movements"), path("reposicion/", views.replenishment, name="replenishment"), path("api/v1/productos/", ProductListAPI.as_view(), name="api-products"), path("api/v1/movimientos/", MovementListCreateAPI.as_view(), name="api-movements")]
