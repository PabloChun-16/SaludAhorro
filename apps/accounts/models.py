from django.db import models

class ExternalUsuario(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    apellido = models.CharField(max_length=150)
    correo_electronico = models.CharField(max_length=255, unique=True)
    password_hash = models.CharField(max_length=255)
    id_rol_id = models.IntegerField()

    class Meta:
        db_table = "mantenimiento_usuarios"
        managed = False  # 👈 clave, para que Django no intente crearla de nuevo

    def __str__(self):
        return self.correo_electronico
