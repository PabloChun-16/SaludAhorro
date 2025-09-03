from django.db import models
from apps.mantenimiento.usuarios.models import Usuario

# Create your models here.
class Roles(models.Model):
    nombre_rol = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.nombre_rol
    
    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

class Laboratorios(models.Model):
    nombre_laboratorio = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return self.nombre_laboratorio
        
    class Meta:
        verbose_name = 'Laboratorio'
        verbose_name_plural = 'Laboratorios'


class Presentaciones(models.Model):
    nombre_presentacion = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nombre_presentacion
        
    class Meta:
        verbose_name = 'Presentación'
        verbose_name_plural = 'Presentaciones'


class Unidades_Medida(models.Model):
    nombre_unidad = models.CharField(max_length=50)
    
    def __str__(self):
        return self.nombre_unidad
        
    class Meta:
        verbose_name = 'Unidad de Medida'
        verbose_name_plural = 'Unidades de Medida'


class Condiciones_Almacenamiento(models.Model):
    nombre_condicion = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nombre_condicion
        
    class Meta:
        verbose_name = 'Condición de Almacenamiento'
        verbose_name_plural = 'Condiciones de Almacenamiento'


class Estado_Alerta(models.Model):
    nombre_estado_alerta = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return self.nombre_estado_alerta
        
    class Meta:
        verbose_name = 'Estado de Alerta'
        verbose_name_plural = 'Estados de Alerta'


class Estado_Lote(models.Model):
    nombre_estado = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return self.nombre_estado
        
    class Meta:
        verbose_name = 'Estado de Lote'
        verbose_name_plural = 'Estados de Lote'


class Estado_Producto(models.Model):
    nombre_estado = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return self.nombre_estado
        
    class Meta:
        verbose_name = 'Estado de Producto'
        verbose_name_plural = 'Estados de Producto'


class Estado_Envio_Receta(models.Model):
    nombre_estado = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.nombre_estado

    class Meta:
        verbose_name = 'Estado de Envío de Receta'
        verbose_name_plural = 'Estados de Envío de Recetas'


class Estado_Movimiento_Inventario(models.Model):
    nombre_estado = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return self.nombre_estado
        
    class Meta:
        verbose_name = 'Estado de Movimiento de Inventario'
        verbose_name_plural = 'Estados de Movimiento de Inventario'


class Estado_Solicitud(models.Model):
    nombre_estado = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return self.nombre_estado
        
    class Meta:
        verbose_name = 'Estado de Solicitud'
        verbose_name_plural = 'Estados de Solicitud'


class Estado_Vencimiento(models.Model):
    nombre_estado = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return self.nombre_estado
        
    class Meta:
        verbose_name = 'Estado de Vencimiento'
        verbose_name_plural = 'Estados de Vencimiento'


class Estado_Recepcion(models.Model):
    nombre_estado = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.nombre_estado

    class Meta:
        verbose_name = 'Estado de Recepción'
        verbose_name_plural = 'Estados de Recepción'


class Tipo_Movimiento_Inventario(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    descripcion = models.CharField(max_length=120, null=True, blank=True)
    naturaleza = models.SmallIntegerField()
    
    def __str__(self):
        return self.codigo
        
    class Meta:
        verbose_name = 'Tipo de Movimiento de Inventario'
        verbose_name_plural = 'Tipos de Movimiento de Inventario'


class Tipo_Alerta(models.Model):
    nombre_tipo_alerta = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return self.nombre_tipo_alerta
        
    class Meta:
        verbose_name = 'Tipo de Alerta'
        verbose_name_plural = 'Tipos de Alerta'


class Auditoria(models.Model):
    accion = models.CharField(max_length=255)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    tabla_afectada = models.CharField(max_length=100, null=True, blank=True)
    id_registro_afectado = models.IntegerField(null=True, blank=True)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)  # 👈 cambio aquí

    def __str__(self):
        return f'{self.accion} - {self.fecha_hora}'
    
    class Meta:
        verbose_name = 'Auditoría'
        verbose_name_plural = 'Auditorías'