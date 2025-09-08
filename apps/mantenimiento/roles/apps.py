from django.apps import AppConfig


class RolesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mantenimiento.roles'
    label = "mnt_roles"
    verbose_name = "Roles"
