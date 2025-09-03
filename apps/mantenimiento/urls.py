from django.urls import path, include
from . import views

app_name = "mantenimiento"

urlpatterns = [
    path("", views.index, name="index"),
    path("usuarios/", include("apps.mantenimiento.usuarios.urls", namespace="mantenimiento_usuarios")),
    path("roles/", views.roles, name="roles"),
    path("laboratorios/", views.laboratorios, name="laboratorios"),
    path("presentaciones/", views.presentaciones, name="presentaciones"),
    path("unidades_medida/", views.unidades_medida, name="unidades_medida"),
    path("condiciones_almacenamiento/", views.condiciones_almacenamiento, name="condiciones_almacenamiento"),
]
