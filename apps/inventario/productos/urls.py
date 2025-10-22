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

    # 🆕 Nuevas rutas para Kardex
    path("<int:pk>/kardex/", views.kardex_modal, name="kardex_modal"),  # modal para fechas
    path("<int:pk>/kardex/resultado/", views.kardex_resultado, name="kardex_resultado"),  # resultado del kardex
    path("<int:pk>/kardex/exportar/", views.kardex_exportar, name="kardex_exportar"),

]
