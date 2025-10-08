from django.urls import path
from . import views

app_name = "lotes"

urlpatterns = [
    path("", views.lista_lotes, name="lista"),
    path("consultar/<int:id>/", views.consultar_lote, name="consultar"),
    path("editar/<int:id>/", views.editar_lote, name="editar"),
    path("eliminar/<int:id>/", views.eliminar_lote, name="eliminar"),
    path("puede-eliminar/<int:id>/", views.puede_eliminar_lote, name="puede_eliminar"), 
]
