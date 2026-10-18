from django.urls import path
from . import views
from .api import MovementListCreateAPI, ProductListAPI

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("productos/", views.product_list, name="products"),
    path("productos/nuevo/", views.product_create, name="product_create"),
    path("productos/<int:pk>/", views.product_detail, name="product_detail"),
    path("productos/<int:pk>/editar/", views.product_update, name="product_update"),
    path("productos/<int:pk>/estado/", views.product_status, name="product_status"),
    path("movimientos/", views.movements, name="movements"),
    path("reposicion/", views.replenishment, name="replenishment"),
    path("ayuda/", views.guide, name="guide"),
    path("api/v1/productos/", ProductListAPI.as_view(), name="api-products"),
    path("api/v1/movimientos/", MovementListCreateAPI.as_view(), name="api-movements"),
]
