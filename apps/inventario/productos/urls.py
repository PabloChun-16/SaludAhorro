from django.urls import path
from . import views

app_name = "productos"

urlpatterns = [
    path("", views.productos_list, name="lista"),
    path("crear/", views.productos_create, name="crear"),
    path("<int:pk>/consultar/", views.productos_detail, name="consultar"),
    path("<int:pk>/editar/", views.productos_edit, name="editar"),
    path("<int:pk>/inactivar/", views.inactivar_producto, name="inactivar"),
    path("<int:pk>/activar/", views.activar_producto, name="activar"), 
]
