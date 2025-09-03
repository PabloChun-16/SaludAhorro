from django.db import models
from apps.mantenimiento.models import Estado_Solicitud
from apps.inventario.models import Productos
from apps.mantenimiento.usuarios.models import Usuario



# Create your models here.
class Solicitudes_Faltantes(models.Model):
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    nombre_documento = models.CharField(max_length=255)
    
    # Relaciones de llave foránea
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    id_estado_solicitud = models.ForeignKey(Estado_Solicitud, on_delete=models.CASCADE)
    
    def __str__(self):
        return f'Solicitud de Faltantes {self.id}'

    class Meta:
        verbose_name = 'Solicitud de Faltantes'
        verbose_name_plural = 'Solicitudes de Faltantes'

class Detalle_Solicitud_Faltantes(models.Model):
    cantidad_solicitada = models.IntegerField()
    es_urgente = models.BooleanField(null=True, blank=True)
    observaciones = models.CharField(max_length=255, null=True, blank=True)

    # Relaciones de llave foránea
    id_solicitud = models.ForeignKey(Solicitudes_Faltantes, on_delete=models.CASCADE)
    id_producto = models.ForeignKey(Productos, on_delete=models.CASCADE)
    
    def __str__(self):
        return f'Detalle de Solicitud {self.id_solicitud.id} - Producto {self.id_producto.nombre}'

    class Meta:
        verbose_name = 'Detalle de Solicitud de Faltantes'
        verbose_name_plural = 'Detalles de Solicitud de Faltantes'
