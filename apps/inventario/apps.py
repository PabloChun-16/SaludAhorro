from django.apps import AppConfig

class InventarioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.inventario"

    def ready(self):
        # si tienes signals, se importan aquí
        from . import signals  # noqa: F401