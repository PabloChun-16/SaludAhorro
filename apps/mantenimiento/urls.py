from django.urls import path, include
from django.views.generic import TemplateView
from . import views

app_name = "mantenimiento"

urlpatterns = [
    path("", views.index, name="index"),
    path("usuarios/", include("apps.mantenimiento.usuarios.urls", namespace="mantenimiento_usuarios")),
    path("roles/", views.roles, name="roles"),
    path('laboratorios/', include(('apps.mantenimiento.laboratorios.urls', 'laboratorios'), namespace='laboratorios')),
    path("presentaciones/", views.presentaciones, name="presentaciones"),
    path("unidades_medida/", views.unidades_medida, name="unidades_medida"),
    path("condiciones_almacenamiento/", views.condiciones_almacenamiento, name="condiciones_almacenamiento"),
]
