from django.apps import AppConfig

class SalidasConfig(AppConfig):
    name = "apps.salidas_devoluciones.salidas"
    label = "salidas_subapp"       # evitar colisiones de etiqueta
    verbose_name = "Salidas"
