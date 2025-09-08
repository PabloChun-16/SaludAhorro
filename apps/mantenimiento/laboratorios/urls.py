from django.urls import path
from . import views

<<<<<<< HEAD
app_name = "laboratorios"

urlpatterns = [
    path("", views.lista_laboratorios, name="lista"),
    path("crear/", views.crear_laboratorio, name="crear_laboratorio"),
    path("<int:pk>/consultar/", views.consultar_laboratorio, name="consultar_laboratorio"),
    path("<int:pk>/editar/", views.editar_laboratorio, name="editar_laboratorio"),
    path("<int:pk>/eliminar/", views.eliminar_laboratorio, name="eliminar_laboratorio"),
]
=======
app_name = "mantenimiento_laboratorios"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("lista/", views.LaboratorioListView.as_view(), name="lista"),
]
>>>>>>> 8f1bf632157c62fc82b9665437497b376869f702
