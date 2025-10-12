from django.urls import path, include
from . import views

app_name = "ajustes_inventario"

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "ingresos/",
        include(("apps.ajustes_inventario.ingresos.urls", "ingresos"),
                namespace="ingresos")
    ),
    path(
        "salidas/",
        include(("apps.ajustes_inventario.salidasAjustes.urls", "salidasAjustes"),
                namespace="salidasAjustes")
    ),
]
