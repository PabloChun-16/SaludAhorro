from django.urls import path
from . import views

app_name = "mantenimiento_presentaciones"

urlpatterns = [
    path("", views.lista_presentaciones, name="lista"),
    path("crear/", views.crear_presentacion, name="crear"),
    path("<int:pk>/consultar/", views.consultar_presentacion, name="consultar"),
    path("<int:pk>/editar/", views.editar_presentacion, name="editar"),
    path("<int:pk>/eliminar/", views.eliminar_presentacion, name="eliminar"),
]