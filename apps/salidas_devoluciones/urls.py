from django.urls import path, include
from . import views

app_name = "sd"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("salidas/", include(("apps.salidas_devoluciones.salidas.urls", "salidas"), namespace="salidas")),
    path("devoluciones/", include(("apps.salidas_devoluciones.devoluciones.urls", "devoluciones"), namespace="devoluciones")),
]
