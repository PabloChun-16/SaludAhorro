from django.contrib import admin
from .models import Alertas_Inventario, Reportes_Vencimiento, Detalle_Reporte_Vencimiento

# Register your models here.
admin.site.register(Alertas_Inventario)
admin.site.register(Reportes_Vencimiento)
admin.site.register(Detalle_Reporte_Vencimiento)
