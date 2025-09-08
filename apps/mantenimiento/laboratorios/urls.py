from django.urls import path
from . import views

app_name = "laboratorios"

urlpatterns = [
    path("", views.lista_laboratorios, name="lista"),
    path("crear/", views.crear_laboratorio, name="crear_laboratorio"),
    path("<int:pk>/consultar/", views.consultar_laboratorio, name="consultar_laboratorio"),
    path("<int:pk>/editar/", views.editar_laboratorio, name="editar_laboratorio"),
    path("<int:pk>/eliminar/", views.eliminar_laboratorio, name="eliminar_laboratorio"),
]