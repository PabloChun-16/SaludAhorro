from django.urls import path
from . import views

# Cambia el app_name para que coincida con el namespace
app_name = "condicionesalmacenamiento"

urlpatterns = [
    path("", views.condiciones_list, name="lista"),
    path("crear/", views.condiciones_create, name="crear"),
    path("<int:pk>/consultar/", views.condiciones_detail, name="consultar"),
    path("<int:pk>/editar/", views.condiciones_edit, name="editar"),
    path("<int:pk>/eliminar/", views.condiciones_delete, name="eliminar"),
]