from django.contrib import admin
from .models import Roles, Presentaciones, Unidades_Medida, Condiciones_Almacenamiento, Estado_Lote, Estado_Producto, Estado_Envio_Receta, Estado_Movimiento_Inventario, Estado_Solicitud, Estado_Vencimiento, Estado_Recepcion, Tipo_Movimiento_Inventario, Auditoria
from apps.mantenimiento.laboratorios.models import Laboratorio

# Register your models here.
admin.site.register(Roles)
admin.site.register(Laboratorio)
admin.site.register(Presentaciones)
admin.site.register(Unidades_Medida)
admin.site.register(Condiciones_Almacenamiento)
admin.site.register(Estado_Lote)
admin.site.register(Estado_Producto)
admin.site.register(Estado_Envio_Receta)
admin.site.register(Estado_Movimiento_Inventario)
admin.site.register(Estado_Solicitud)
admin.site.register(Estado_Vencimiento)
admin.site.register(Estado_Recepcion)
admin.site.register(Tipo_Movimiento_Inventario)
admin.site.register(Auditoria)

