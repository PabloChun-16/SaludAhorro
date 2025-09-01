from django.db import models
from apps.mantenimiento.models import Usuarios, Estado_Recepcion
from apps.inventario.models import Lotes

# Create your models here.

class Recepciones_Envio(models.Model):
    fecha_recepcion = models.DateTimeField(auto_now_add=True)
    numero_envio_bodega = models.CharField(max_length=100, null=True, blank=True)
    
    # Relaciones de llave foránea
    id_usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE)
    estado_recepcion = models.ForeignKey(Estado_Recepcion, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'Recepción {self.id} - {self.fecha_recepcion}'
        
    class Meta:
        verbose_name = 'Recepción de Envío'
        verbose_name_plural = 'Recepciones de Envío'


class Detalle_Recepcion(models.Model):
    cantidad_recibida = models.IntegerField()
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Relaciones de llave foránea
    id_recepcion = models.ForeignKey(Recepciones_Envio, on_delete=models.CASCADE)
    id_lote = models.ForeignKey(Lotes, on_delete=models.CASCADE)

    def __str__(self):
        return f'Detalle de Recepción {self.id_recepcion.id} - Lote {self.id_lote.numero_lote}'
        
    class Meta:
        verbose_name = 'Detalle de Recepción'
        verbose_name_plural = 'Detalles de Recepción'
