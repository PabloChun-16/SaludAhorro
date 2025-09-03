from django.apps import AppConfig

class UsuariosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.mantenimiento.usuarios"   # ruta completa del paquete
    label = "mnt_usuarios"            # etiqueta única para evitar colisiones
    verbose_name = "Usuarios"
