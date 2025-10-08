from django.urls import path, include
from . import views

app_name = "inventario"

urlpatterns = [
    path("", views.index, name="index"),

    # Submódulo de Productos
    path("productos/", include(("apps.inventario.productos.urls", "productos"), namespace="productos")),
    # Submódulo de Stock
    path("stock/", include(("apps.inventario.stock.urls", "stock"), namespace="stock")),
    # Submódulo de Lotes
    path("lotes/", include(("apps.inventario.lotes.urls", "lotes"), namespace="lotes")),
]
