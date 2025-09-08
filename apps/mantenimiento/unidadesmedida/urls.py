from django.urls import path
from . import views

app_name = "mantenimiento_unidadesmedida"

urlpatterns = [
    path("", views.unidades_list, name="lista"),
    path("crear/", views.unidades_create, name="crear"),
    path("<int:pk>/consultar/", views.unidades_detail, name="consultar"),
    path("<int:pk>/editar/", views.unidades_edit, name="editar"),
    path("<int:pk>/eliminar/", views.unidades_delete, name="eliminar"),
]

