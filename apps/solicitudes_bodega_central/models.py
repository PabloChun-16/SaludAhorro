from django.db import models
from django.utils import timezone
from apps.mantenimiento.models import Estado_Solicitud
from apps.inventario.models import Productos
from apps.mantenimiento.usuarios.models import Usuario


class Solicitudes_Faltantes(models.Model):
    fecha_solicitud = models.DateTimeField(default=timezone.now)
    nombre_documento = models.CharField(max_length=255)
    
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="solicitudes_faltantes")
    id_estado_solicitud = models.ForeignKey(Estado_Solicitud, on_delete=models.CASCADE, related_name="solicitudes_estado")
    
    def __str__(self):
        return f'{self.nombre_documento} ({self.id_usuario})'

    class Meta:
        verbose_name = 'Solicitud de Faltantes'
        verbose_name_plural = 'Solicitudes de Faltantes'


class Detalle_Solicitud_Faltantes(models.Model):
    cantidad_solicitada = models.PositiveIntegerField()
    es_urgente = models.BooleanField(default=False)
    observaciones = models.CharField(max_length=255, null=True, blank=True)

    id_solicitud = models.ForeignKey(Solicitudes_Faltantes, on_delete=models.CASCADE, related_name="detalles")
    id_producto = models.ForeignKey(Productos, on_delete=models.CASCADE, related_name="solicitudes_producto")
    
    def __str__(self):
        return f'{self.id_producto.nombre} ({self.cantidad_solicitada})'

    class Meta:
        verbose_name = 'Detalle de Solicitud de Faltantes'
        verbose_name_plural = 'Detalles de Solicitud de Faltantes'
