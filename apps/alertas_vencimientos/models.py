from django.db import models
from apps.mantenimiento.models import Estado_Vencimiento
from apps.mantenimiento.usuarios.models import Usuario
from apps.inventario.models import Lotes

# Create your models here.
class Reportes_Vencimiento(models.Model):
    fecha_reporte = models.DateField(auto_now_add=True)
    observaciones = models.CharField(max_length=255, null=True, blank=True)
    documento = models.CharField(max_length=255)

    # Relaciones de llave foránea
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    id_estado = models.ForeignKey(Estado_Vencimiento, on_delete=models.CASCADE)
    
    def __str__(self):
        return f'Reporte de Vencimiento {self.id}'

    class Meta:
        verbose_name = 'Reporte de Vencimiento'
        verbose_name_plural = 'Reportes de Vencimiento'


class Detalle_Reporte_Vencimiento(models.Model):
    cantidad_reportada = models.IntegerField()
    
    # Relaciones de llave foránea
    id_reporte = models.ForeignKey(Reportes_Vencimiento, on_delete=models.CASCADE)
    id_lote = models.ForeignKey(Lotes, on_delete=models.CASCADE)

    def __str__(self):
        return f'Detalle Reporte {self.id_reporte.id} - Lote {self.id_lote.numero_lote}'
        
    class Meta:
        verbose_name = 'Detalle de Reporte de Vencimiento'
        verbose_name_plural = 'Detalles de Reporte de Vencimiento'
