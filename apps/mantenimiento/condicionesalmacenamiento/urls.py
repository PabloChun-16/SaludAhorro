from django.urls import path
from . import views

app_name = "mantenimiento_condicionesalmacenamiento"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("lista/", views.CondicionAlmacenamientoListView.as_view(), name="lista"),
]
