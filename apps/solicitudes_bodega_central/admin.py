from django.contrib import admin
from .models import Solicitudes_Faltantes, Detalle_Solicitud_Faltantes


@admin.register(Solicitudes_Faltantes)
class SolicitudesFaltantesAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_documento', 'id_usuario', 'fecha_solicitud', 'id_estado_solicitud')
    list_filter = ('id_estado_solicitud', 'fecha_solicitud')
    search_fields = ('nombre_documento', 'id_usuario__username')
    ordering = ('-fecha_solicitud',)


@admin.register(Detalle_Solicitud_Faltantes)
class DetalleSolicitudFaltantesAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_solicitud', 'id_producto', 'cantidad_solicitada', 'es_urgente')
    list_filter = ('es_urgente',)
    search_fields = ('id_producto__nombre', 'observaciones')