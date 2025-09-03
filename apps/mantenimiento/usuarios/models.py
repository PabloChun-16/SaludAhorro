from django.db import models

class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo_electronico = models.CharField(max_length=255, unique=True)
    password_hash = models.CharField(max_length=255)
    id_rol = models.ForeignKey(
        "mantenimiento.Roles",  # ✅ referencia por string a la app y modelo
        on_delete=models.CASCADE,
        db_column="id_rol_id"
    )

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    class Meta:
        db_table = "mantenimiento_usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

