from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

class LoginRequiredMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            return None

        path = request.path

        # Exact matches (home, login, logout)
        if path in getattr(settings, "LOGIN_EXEMPT_EXACT", []):
            return None

        # Prefix matches (blog/, contacto/, etc.)
        for prefix in getattr(settings, "LOGIN_EXEMPT_PREFIXES", []):
            if path.startswith(prefix):
                return None

        # Deja pasar archivos estáticos y media en dev
        if path.startswith(getattr(settings, "STATIC_URL", "/static/")):
            return None
        if path.startswith(getattr(settings, "MEDIA_URL", "/media/")):
            return None

        # Página de admin login (opcional)
        if path.startswith("/admin/login/"):
            return None

        # Si no está autenticado → manda a login
        return redirect(f'{reverse("login")}?next={path}')
