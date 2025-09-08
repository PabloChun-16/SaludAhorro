from django.urls import path, include
from django.views.generic import TemplateView
from . import views

app_name = "mantenimiento"

urlpatterns = [
    path("", views.index, name="index"),
<<<<<<< HEAD
    path("usuarios/", include("apps.mantenimiento.usuarios.urls", namespace="mantenimiento_usuarios")),
    path("roles/", views.roles, name="roles"),
    path('laboratorios/', include(('apps.mantenimiento.laboratorios.urls', 'laboratorios'), namespace='laboratorios')),
    path("presentaciones/", views.presentaciones, name="presentaciones"),
    path("unidades_medida/", views.unidades_medida, name="unidades_medida"),
    path("condiciones_almacenamiento/", views.condiciones_almacenamiento, name="condiciones_almacenamiento"),
=======

    path("usuarios/",
         include(("apps.mantenimiento.usuarios.urls", "mantenimiento_usuarios"),
                 namespace="mantenimiento_usuarios")),
    path("roles/",
         include(("apps.mantenimiento.roles.urls", "mantenimiento_roles"),
                 namespace="mantenimiento_roles")),
    path("laboratorios/",
         include(("apps.mantenimiento.laboratorios.urls", "mantenimiento_laboratorios"),
                 namespace="mantenimiento_laboratorios")),
    path("presentaciones/",
         include(("apps.mantenimiento.presentaciones.urls", "mantenimiento_presentaciones"),
                 namespace="mantenimiento_presentaciones")),
    path("unidades-medida/",
         include(("apps.mantenimiento.unidadesmedida.urls", "mantenimiento_unidadesmedida"),
                 namespace="mantenimiento_unidadesmedida")),
    path("condiciones-almacenamiento/",
         include(("apps.mantenimiento.condicionesalmacenamiento.urls", "mantenimiento_condicionesalmacenamiento"),
                 namespace="mantenimiento_condicionesalmacenamiento")),
>>>>>>> 8f1bf632157c62fc82b9665437497b376869f702
]
