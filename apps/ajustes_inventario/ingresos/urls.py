from django.urls import path
from . import views

app_name = "ingresos"

urlpatterns = [
    path("", views.ajuste_ingreso_list, name="ajuste_ingreso_list"),
    path("crear/", views.ajuste_ingreso_create, name="ajuste_ingreso_create"),
    path("productos/search/", views.search_productos, name="search_productos"),
    path("lotes/<int:producto_id>/search/", views.search_lotes, name="search_lotes"),
    path("lotes/create/", views.create_lote, name="create_lote"),
    path("consultar/<int:ajuste_id>/", views.ajuste_ingreso_detail, name="ajuste_ingreso_detail"),
    path("exportar/<int:ajuste_id>/", views.ajuste_ingreso_export_pdf, name="ajuste_ingreso_export_pdf"),
    path("anular/<int:ajuste_id>/", views.anular_ajuste_ingreso, name="ajuste_ingreso_anular"),

]
