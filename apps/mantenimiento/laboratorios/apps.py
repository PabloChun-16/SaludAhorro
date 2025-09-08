from django.apps import AppConfig

<<<<<<< HEAD
class LaboratoriosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mantenimiento.laboratorios'

=======

class LaboratoriosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mantenimiento.laboratorios'
    label = "mnt_laboratorios"
    verbose_name = "Laboratorios"
>>>>>>> 8f1bf632157c62fc82b9665437497b376869f702
