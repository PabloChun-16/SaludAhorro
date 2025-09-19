from django.urls import path
from . import views

app_name = "recepcion"

urlpatterns = [
    path("", views.recepcion_list, name="lista"),
    path("crear/", views.recepcion_create, name="crear"),
    path("<int:pk>/consultar/", views.recepcion_detail, name="consultar"),
    path("productos/search/", views.search_productos, name="search_productos"),
    path("lotes/<int:producto_id>/search/", views.search_lotes, name="search_lotes"),
    path("lotes/create/", views.create_lote, name="create_lote"),
]
