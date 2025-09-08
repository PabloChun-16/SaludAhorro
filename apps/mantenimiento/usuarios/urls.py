from django.urls import path
from . import views

app_name = "mantenimiento_usuarios"

urlpatterns = [
    path("", views.UsuarioListView.as_view(), name="lista"),
    path("nuevo/", views.usuario_create_modal, name="crear"),               # GET: form parcial · POST: crea
    path("<int:pk>/editar/", views.usuario_update_modal, name="editar"),    # GET: form parcial · POST: actualiza
    path("<int:pk>/eliminar/", views.usuario_delete_modal, name="eliminar"),# GET: confirm · POST: elimina (o baja lógica)
    path("<int:pk>/consultar/", views.usuario_consultar_modal, name="consultar"), # GET: consulta usuario
]
