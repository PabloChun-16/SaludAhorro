from django.urls import path
from . import views

app_name = "mantenimiento_presentaciones"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("lista/", views.PresentacionListView.as_view(), name="lista"),
]
