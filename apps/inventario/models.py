from django.db import models
from apps.mantenimiento.models import Laboratorio, Presentaciones, Unidades_Medida, Condiciones_Almacenamiento, Estado_Producto, Estado_Lote


# Create your models here.
class Productos(models.Model):
    codigo_producto = models.CharField(max_length=255)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(null=True, blank=True)
    imagen_url = models.ImageField(upload_to="productos/", blank=True, null=True)
    requiere_receta = models.BooleanField(null=True, blank=True)
    es_controlado = models.BooleanField(null=True, blank=True)
    stock_minimo = models.IntegerField(default=0, null=True, blank=True)
    
    # Relaciones de llave foránea a las tablas de Mantenimiento
    id_laboratorio = models.ForeignKey(Laboratorio, on_delete=models.SET_NULL, null=True, blank=True)
    id_unidad_medida = models.ForeignKey(Unidades_Medida, on_delete=models.CASCADE)
    id_presentacion = models.ForeignKey(Presentaciones, on_delete=models.CASCADE)
    id_condicion_almacenamiento = models.ForeignKey(Condiciones_Almacenamiento, on_delete=models.SET_NULL, null=True, blank=True)
    id_estado_producto = models.ForeignKey(
        Estado_Producto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=1   # 🔹 Asumiendo que el ID=1 es "Activo"
    )
    
    def __str__(self):
        return self.nombre
        
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'


class Lotes(models.Model):
    # Relaciones de llave foránea
    id_producto = models.ForeignKey(Productos, on_delete=models.CASCADE)
    id_estado_lote = models.ForeignKey(Estado_Lote, on_delete=models.SET_NULL, null=True, blank=True)

    # Campos propios del modelo Lotes
    numero_lote = models.CharField(max_length=100)
    fecha_caducidad = models.DateField()
    cantidad_disponible = models.IntegerField()
    ubicacion_almacen = models.CharField(max_length=100, null=True, blank=True)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f'Lote {self.numero_lote} de {self.id_producto.nombre}'
    
    class Meta:
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'
        constraints = [
            models.UniqueConstraint(
                fields=['id_producto', 'numero_lote'],
                name='uq_lotes_producto_numero'
            )
        ]

