from django.urls import path
from . import views

app_name = "mantenimiento_roles"

urlpatterns = [
    path("", views.RolListView.as_view(), name="index"),
    path("lista/", views.RolListView.as_view(), name="lista"),
    path("crear/", views.rol_crear, name="crear"),
    path("<int:pk>/consultar/", views.rol_consultar, name="consultar"),
    path("<int:pk>/editar/", views.rol_editar, name="editar"),
    path("<int:pk>/eliminar/", views.rol_eliminar, name="eliminar"),
]
