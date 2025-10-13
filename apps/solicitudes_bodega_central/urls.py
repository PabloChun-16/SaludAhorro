from django.shortcuts import redirect
from django.urls import path
from . import views

app_name = "solicitudes_bodega_central"

urlpatterns = [
    path("", views.index, name="index"),
    
    path("registrar/", views.registrar_solicitud, name="registrar_solicitud"),
    path("crear/", views.crear_solicitud, name="crear_solicitud"),
    path("<int:id>/editar/", views.editar_solicitud, name="editar_solicitud"),
    path("<int:id>/eliminar/", views.eliminar_solicitud, name="eliminar_solicitud"),
    path("<int:id>/obtener/", views.obtener_solicitud, name="obtener_solicitud"),
    
     path('listar/', views.listar_solicitudes, name='listar_solicitudes'),
    path('exportar/pdf/', views.exportar_solicitudes_pdf, name='exportar_solicitudes_pdf'),
]
