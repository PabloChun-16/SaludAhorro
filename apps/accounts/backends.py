from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.db import transaction
from .models import ExternalUsuario
import bcrypt

class ExternalUsuariosBackend(BaseBackend):
    """
    Autentica contra la tabla externa mantenimiento_usuarios.
    El 'username' que recibe será el email del usuario.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        try:
            ext = ExternalUsuario.objects.get(correo_electronico=username)
        except ExternalUsuario.DoesNotExist:
            return None

        # Verifica el hash (ajusta si tu hash no es bcrypt)
        try:
            if not bcrypt.checkpw(password.encode("utf-8"), ext.password_hash.encode("utf-8")):
                return None
        except ValueError:
            # Si el formato del hash no es válido para bcrypt
            return None

        # Mapea rol a permisos básicos de Django (ajústalo a tu lógica)
        is_staff = bool(ext.id_rol_id == 1)   # p.ej. rol 1 = admin
        is_superuser = False                  # ajusta si procede

        # Crea/actualiza el usuario de Django “espejo”
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username=ext.correo_electronico,
                defaults={
                    "first_name": ext.nombre[:150],
                    "last_name": ext.apellido[:150],
                    "email": ext.correo_electronico,
                    "is_active": True,
                    "is_staff": is_staff,
                    "is_superuser": is_superuser,
                },
            )
            # Sincroniza datos cada login (opcional)
            if not created:
                user.first_name = ext.nombre[:150]
                user.last_name = ext.apellido[:150]
                user.email = ext.correo_electronico
                user.is_active = True
                user.is_staff = is_staff
                user.is_superuser = is_superuser
                user.save()

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
