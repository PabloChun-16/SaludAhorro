from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='ajustes_inventario_index'),
]
