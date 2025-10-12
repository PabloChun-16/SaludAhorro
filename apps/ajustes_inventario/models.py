from django.db import models
from apps.mantenimiento.usuarios.models import Usuario
from apps.inventario.models import Lotes

# Create your models here.
class Inventario_Fisico(models.Model):
    fecha_conteo = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=50)

    TIPO_AJUSTE_CHOICES = [
    ('Ingreso', 'Ingreso'),
    ('Salida', 'Salida'),
]
    tipo_ajuste = models.CharField(
    max_length=20,
    choices=TIPO_AJUSTE_CHOICES,
    default='Ingreso',
)
    
    # Relación de llave foránea
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    
    def __str__(self):
        return f'Conteo Físico {self.id} - {self.fecha_conteo}'
    
    class Meta:
        verbose_name = 'Inventario Físico'
        verbose_name_plural = 'Inventarios Físicos'


class Detalle_Conteo(models.Model):
    cantidad_sistema = models.IntegerField()
    cantidad_contada = models.IntegerField()
    diferencia = models.IntegerField()

    # Relaciones de llave foránea
    id_conteo = models.ForeignKey(Inventario_Fisico, on_delete=models.CASCADE)
    id_lote = models.ForeignKey(Lotes, on_delete=models.CASCADE)
    
    def __str__(self):
        return f'Detalle de Conteo {self.id_conteo.id} - Lote {self.id_lote.numero_lote}'
        
    class Meta:
        verbose_name = 'Detalle de Conteo'
        verbose_name_plural = 'Detalles de Conteo'
