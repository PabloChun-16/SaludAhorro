from django.db import models
from apps.mantenimiento.models import Estado_Envio_Receta
from apps.mantenimiento.usuarios.models import Usuario
from apps.inventario.models import Productos

# Create your models here.
class Recetas_Medicas(models.Model):
    fecha_venta = models.DateTimeField(auto_now_add=True)
    referencia_factura = models.CharField(max_length=255, null=True, blank=True)
    referente_receta = models.CharField(max_length=255, null=True, blank=True)

    # Relaciones de llave foránea
    id_producto = models.ForeignKey(Productos, on_delete=models.CASCADE)
    id_usuario_venta = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    
    def __str__(self):
        return f'Receta {self.id} - Factura {self.referencia_factura}'

    class Meta:
        verbose_name = 'Receta Médica'
        verbose_name_plural = 'Recetas Médicas'


class Envios_Recetas(models.Model):
    fecha_envio = models.DateTimeField(auto_now_add=True)
    nombre_reporte = models.CharField(max_length=255, null=True, blank=True)

    # Relaciones de llave foránea
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    id_estado_envio = models.ForeignKey(Estado_Envio_Receta, on_delete=models.CASCADE)

    def __str__(self):
        return f'Envío de Recetas {self.id}'
    
    class Meta:
        verbose_name = 'Envío de Receta'
        verbose_name_plural = 'Envío de Recetas'


class Detalle_Envio_Recetas(models.Model):
    # Relaciones de llave foránea
    id_envio = models.ForeignKey(Envios_Recetas, on_delete=models.CASCADE)
    id_receta = models.ForeignKey(Recetas_Medicas, on_delete=models.CASCADE)

    def __str__(self):
        return f'Detalle Envío {self.id_envio.id} - Receta {self.id_receta.id}'
    
    class Meta:
        verbose_name = 'Detalle de Envío de Recetas'
        verbose_name_plural = 'Detalles de Envío de Recetas'
