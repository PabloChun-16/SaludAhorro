from django.urls import path
from . import views

app_name = "mantenimiento_laboratorios"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("lista/", views.LaboratorioListView.as_view(), name="lista"),
]
