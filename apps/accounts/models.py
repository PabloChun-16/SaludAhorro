from django.db import models

class ExternalUsuario(models.Model):
    id = models.BigAutoField(primary_key=True)  # ajusta si es int normal
    nombre = models.CharField(max_length=150)
    apellido = models.CharField(max_length=150)
    correo_electronico = models.CharField(max_length=255, unique=True)
    password_hash = models.CharField(max_length=255)
    id_rol_id = models.IntegerField()  # ajusta si es FK real

    class Meta:
        db_table = "mantenimiento_usuarios"
        managed = False  # ¡Clave! Django NO crea ni migra esta tabla

    def __str__(self):
        return self.correo_electronico
