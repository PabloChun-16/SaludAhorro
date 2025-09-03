from django.contrib import admin
from .models import Solicitudes_Faltantes, Detalle_Solicitud_Faltantes

# Register your models here.
admin.site.register(Solicitudes_Faltantes)
admin.site.register(Detalle_Solicitud_Faltantes)