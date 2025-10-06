from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class UsuarioManager(BaseUserManager):
    def create_user(self, correo_electronico, nombre, apellido, password=None, **extra_fields):
        if not correo_electronico:
            raise ValueError("El usuario debe tener un correo electrónico")

        correo_electronico = self.normalize_email(correo_electronico)
        user = self.model(
            correo_electronico=correo_electronico,
            nombre=nombre,
            apellido=apellido,
            **extra_fields
        )
        user.set_password(password)  # maneja hash
        user.save(using=self._db)
        return user

    def create_superuser(self, correo_electronico, nombre, apellido, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuario debe tener is_superuser=True.")

        return self.create_user(correo_electronico, nombre, apellido, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo_electronico = models.EmailField(max_length=255, unique=True)

    id_rol = models.ForeignKey(
        "mantenimiento.Roles",
        on_delete=models.CASCADE,
        db_column="id_rol_id",
        null=True,
        blank=True
    )

    # Campos requeridos por Django
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # necesario para admin

    objects = UsuarioManager()

    USERNAME_FIELD = "correo_electronico"
    REQUIRED_FIELDS = ["nombre", "apellido"]

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    class Meta:
        db_table = "mantenimiento_usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
