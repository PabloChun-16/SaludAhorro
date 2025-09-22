from django.db import models

class Producto(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=255)  # ajusta al campo real

    class Meta:
        db_table = 'inventario_productos'
        managed = False

    def __str__(self):
        return self.nombre


class Usuario(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=255)

    class Meta:
        db_table = 'mantenimiento_usuarios'
        managed = False

    def __str__(self):
        return self.nombre


class EstadoEnvioReceta(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre_estado = models.CharField(max_length=255)

    class Meta:
        db_table = 'mantenimiento_estado_envio_receta'
        managed = False

    def __str__(self):
        return self.nombre_estado


# =========================
# Tablas del módulo recetas
# =========================

class RecetaMedica(models.Model):
    id = models.BigAutoField(primary_key=True)
    fecha_venta = models.DateTimeField(auto_now_add=True)
    referencia_factura = models.CharField(max_length=255, null=True, blank=True)
    referente_receta = models.CharField(max_length=255, null=True, blank=True)
    id_producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column='id_producto_id')
    id_usuario_venta = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='id_usuario_venta_id')

    class Meta:
        db_table = 'recetas_recetas_medicas'

    def __str__(self):
        return f"Receta {self.referencia_factura or ''} - {self.referente_receta or ''}"


class EnvioReceta(models.Model):
    id = models.BigAutoField(primary_key=True)
    fecha_envio = models.DateTimeField()
    nombre_reporte = models.CharField(max_length=255, null=True, blank=True)
    id_estado_envio = models.ForeignKey(EstadoEnvioReceta, on_delete=models.CASCADE, db_column='id_estado_envio_id')
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='id_usuario_id')

    class Meta:
        db_table = 'recetas_envios_recetas'

    def __str__(self):
        return f"Envío {self.nombre_reporte or ''} - {self.fecha_envio}"


class DetalleEnvioReceta(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_envio = models.ForeignKey(EnvioReceta, on_delete=models.CASCADE, db_column='id_envio_id')
    id_receta = models.ForeignKey(RecetaMedica, on_delete=models.CASCADE, db_column='id_receta_id')

    class Meta:
        db_table = 'recetas_detalle_envio_recetas'

    def __str__(self):
        return f"Detalle envío {self.id_envio_id} - receta {self.id_receta_id}"