from django.urls import path
from . import views

app_name = "lotes"

urlpatterns = [
    path("", views.lista_lotes, name="lista"),
    path("consultar/<int:id>/", views.consultar_lote, name="consultar"),
    path("editar/<int:id>/", views.editar_lote, name="editar"),

    path("retirar/<int:id>/", views.retirar_lote, name="retirar"),
    path("puede-retirar/<int:id>/", views.puede_retirar_lote, name="puede_retirar"), 

]
