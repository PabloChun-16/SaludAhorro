from django.contrib import admin
from .models import RecetaMedica, EnvioReceta, DetalleEnvioReceta


@admin.register(RecetaMedica)
class RecetaMedicaAdmin(admin.ModelAdmin):
    list_display = ('id', 'referencia_factura', 'referente_receta', 'fecha_venta')


@admin.register(EnvioReceta)
class EnvioRecetaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_reporte', 'fecha_envio')


@admin.register(DetalleEnvioReceta)
class DetalleEnvioRecetaAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_envio', 'id_receta')