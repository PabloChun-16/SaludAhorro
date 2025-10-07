# apps/recepcion_almacenamiento/urls.py
from django.urls import path
from . import views

app_name = "recepcion"

urlpatterns = [
    path("", views.recepcion_list, name="recepcion_list"),
    path("crear/", views.recepcion_create, name="recepcion_create"),
    path("<int:pk>/", views.recepcion_detail, name="recepcion_detail"),
    path("productos/search/", views.search_productos, name="search_productos"),
    path("lotes/<int:producto_id>/search/", views.search_lotes, name="search_lotes"),
    path("lotes/create/", views.create_lote, name="create_lote"),
]
