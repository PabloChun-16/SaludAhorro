from django.urls import path
from . import views

app_name = "solicitudes_bodega_central"

urlpatterns = [
    # Home del módulo
    path("", views.index, name="index"),

    # Pantalla principal con el formulario embebido
    path("registrar/", views.registrar_solicitud, name="registrar_solicitud"),

    # Crear (POST JSON). Si llega GET se redirige a 'registrar_solicitud'
    path("crear/", views.crear_solicitud, name="crear_solicitud"),

    # Buscador AJAX para el input de productos (usa {% url 'solicitudes_bodega_central:buscar_productos' %})
    path("buscar-productos/", views.buscar_productos, name="buscar_productos"),

    # Rutas que ya tenías
    path("<int:id>/editar/", views.editar_solicitud, name="editar_solicitud"),
    path("<int:id>/eliminar/", views.eliminar_solicitud, name="eliminar_solicitud"),
    path("<int:id>/obtener/", views.obtener_solicitud, name="obtener_solicitud"),

    # Utilidades
    path("listar/", views.listar_solicitudes, name="listar_solicitudes"),
    path("exportar/pdf/", views.exportar_solicitudes_pdf, name="exportar_solicitudes_pdf"),
]
