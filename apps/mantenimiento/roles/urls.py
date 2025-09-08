from django.urls import path
from . import views

app_name = "mantenimiento_roles"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("lista/", views.RolListView.as_view(), name="lista"),
]
