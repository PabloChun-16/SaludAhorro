from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

Usuario = get_user_model()

class ExternalUsuariosBackend(BaseBackend):
    """
    Autentica contra tu AUTH_USER_MODEL (mnt_usuarios.Usuario).
    El 'username' es el correo_electronico.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        try:
            user = Usuario.objects.get(correo_electronico=username)
        except Usuario.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None
