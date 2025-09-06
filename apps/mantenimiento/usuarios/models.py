from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo_electronico = models.CharField(max_length=255, unique=True)
    # 128 es suficiente para pbkdf2 sha256
    password_hash = models.CharField(max_length=128)

    id_rol = models.ForeignKey(
        "mantenimiento.Roles",
        on_delete=models.CASCADE,
        db_column="id_rol_id"
    )

    # === Helpers de password ===
    def set_password(self, raw_password: str) -> None:
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password_hash)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    class Meta:
        db_table = "mantenimiento_usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
