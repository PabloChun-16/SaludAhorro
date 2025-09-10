from django.urls import path, include
from django.views.generic import TemplateView
from . import views

app_name = "mantenimiento"

urlpatterns = [
    path("", views.index, name="index"),
    path("laboratorios/", include(("apps.mantenimiento.laboratorios.urls", "laboratorios"), namespace="mantenimiento_laboratorios")),
    path("roles/", include(("apps.mantenimiento.roles.urls", "roles"), namespace="mantenimiento_roles")),
    path("usuarios/", include(("apps.mantenimiento.usuarios.urls", "usuarios"), namespace="mantenimiento_usuarios")),
    path("presentaciones/", include(("apps.mantenimiento.presentaciones.urls", "presentaciones"), namespace="mantenimiento_presentaciones")),
    path("unidadesmedida/", include(("apps.mantenimiento.unidadesmedida.urls", "unidadesmedida"), namespace="unidadesmedida")),
    path("condicionesalmacenamiento/", include(("apps.mantenimiento.condicionesalmacenamiento.urls", "condicionesalmacenamiento"), namespace="mantenimiento_condicionesalmacenamiento")),
]

