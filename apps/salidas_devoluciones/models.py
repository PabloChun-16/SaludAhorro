from django.db import models
from apps.inventario.models import Lotes
from apps.mantenimiento.models import Tipo_Movimiento_Inventario, Usuarios, Estado_Movimiento_Inventario

# Create your models here.
class Movimientos_Inventario_Sucursal(models.Model):
    cantidad = models.IntegerField()
    fecha_hora = models.DateTimeField(auto_now_add=True)
    referencia_transaccion = models.CharField(max_length=255, null=True, blank=True)
    comentario = models.CharField(max_length=255, null=True, blank=True)
    
    # Relaciones de llave foránea
    id_lote = models.ForeignKey(Lotes, on_delete=models.CASCADE)
    id_tipo_movimiento = models.ForeignKey(Tipo_Movimiento_Inventario, on_delete=models.CASCADE)
    id_usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE)
    estado_movimiento_inventario = models.ForeignKey(Estado_Movimiento_Inventario, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f'Movimiento {self.id_tipo_movimiento.codigo} - Lote {self.id_lote.numero_lote}'
        
    class Meta:
        verbose_name = 'Movimiento de Inventario de Sucursal'
        verbose_name_plural = 'Movimientos de Inventario de Sucursal'
