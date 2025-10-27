from django.urls import path
from . import views

app_name = "vencimientos"

urlpatterns = [
    path("", views.reporte_vencimiento_list, name="reporte_vencimiento_list"),
    path("crear/", views.reporte_vencimiento_create, name="reporte_vencimiento_create"),
    path("consultar/<int:reporte_id>/", views.reporte_vencimiento_detail, name="reporte_vencimiento_detail"),
    path("productos/search/", views.search_productos, name="search_productos"),
    path("lotes/<int:producto_id>/search/", views.search_lotes, name="search_lotes"),

    path("cambiar-estado/modal/<int:reporte_id>/", views.reporte_cambiar_estado_modal, name="reporte_cambiar_estado_modal"),
    path("cambiar-estado/<int:reporte_id>/", views.reporte_cambiar_estado, name="reporte_cambiar_estado"),
]
