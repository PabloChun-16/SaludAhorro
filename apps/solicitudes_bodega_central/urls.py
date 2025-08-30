from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='solicitudes_bodega_central_index'),
]
