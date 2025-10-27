from django.contrib import admin
from .models import Reportes_Vencimiento, Detalle_Reporte_Vencimiento

# Register your models here.
admin.site.register(Reportes_Vencimiento)
admin.site.register(Detalle_Reporte_Vencimiento)
