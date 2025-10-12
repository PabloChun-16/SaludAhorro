from django.urls import path
from . import views

app_name = "salidas"

urlpatterns = [
    path("", views.ajuste_salida_list, name="ajuste_salida_list"),
    path("crear/", views.ajuste_salida_create, name="ajuste_salida_create"),
    path("productos/search/", views.search_productos, name="search_productos"),
    path("lotes/<int:producto_id>/search/", views.search_lotes, name="search_lotes"),
    path("lotes/create/", views.create_lote, name="create_lote"),
    path("consultar/<int:ajuste_id>/", views.ajuste_salida_detail, name="ajuste_salida_detail"),
    path("anular/<int:ajuste_id>/", views.anular_ajuste_salida, name="ajuste_salida_anular"),
]
