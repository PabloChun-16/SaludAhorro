from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib.auth.hashers import check_password, make_password, identify_hasher
from .models import ExternalUsuario  # si en realidad es Usuario, importa ese

class ExternalUsuariosBackend(BaseBackend):
    """
    Autentica contra la tabla externa mantenimiento_usuarios.
    El 'username' es el email.
    Usa el sistema de hash de Django (pbkdf2_sha256 por defecto).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        try:
            ext = ExternalUsuario.objects.get(correo_electronico=username)
        except ExternalUsuario.DoesNotExist:
            return None

        # 1) Verificar contraseña con el hasher de Django
        if not check_password(password, ext.password_hash):
            return None

        # 2) (Opcional pero recomendado) Actualizar el hash si el formato viejo no es el actual
        #    p.ej., si venía de otro algoritmo o texto plano
        try:
            hasher = identify_hasher(ext.password_hash)
        except Exception:
            hasher = None  # hash inválido o texto plano (si ya pasó check_password, era texto plano)
        # Si el hasher no es el default actual, re-hashear
        # Nota: podrías usar hasher.must_update(...) si quieres granularidad.
        if hasher is None or hasher.algorithm != "pbkdf2_sha256":
            ext.password_hash = make_password(password)  # usa el default (pbkdf2_sha256)
            ext.save(update_fields=["password_hash"])

        # 3) Mapear a usuario "espejo" de Django
        is_staff = bool(ext.id_rol_id == 1)   # ajusta tu lógica
        is_superuser = False

        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username=ext.correo_electronico,
                defaults={
                    "first_name": (ext.nombre or "")[:150],
                    "last_name": (ext.apellido or "")[:150],
                    "email": ext.correo_electronico,
                    "is_active": True,
                    "is_staff": is_staff,
                    "is_superuser": is_superuser,
                },
            )
            if not created:
                user.first_name = (ext.nombre or "")[:150]
                user.last_name = (ext.apellido or "")[:150]
                user.email = ext.correo_electronico
                user.is_active = True
                user.is_staff = is_staff
                user.is_superuser = is_superuser
                user.save(update_fields=["first_name", "last_name", "email", "is_active", "is_staff", "is_superuser"])

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
