from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='alertas_vencimientos_index'),
]
