from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib import messages
from functools import wraps

def solo_admin(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': 'Debe iniciar sesión.'}, status=403)
            messages.warning(request, "Debe iniciar sesión para acceder.")
            return redirect(reverse_lazy('login'))

        if not user.id_rol or user.id_rol.nombre_rol.lower() != 'administrador':
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': 'No tiene permisos para realizar esta acción.'}, status=403)
            
            # 🚨 mensaje de advertencia visible al usuario
            messages.warning(request, "Solo los usuarios con rol de Administrador pueden acceder a esta sección.")
            
            return redirect(reverse_lazy('mantenimiento:index'))

        return view_func(request, *args, **kwargs)
    return wrapper
