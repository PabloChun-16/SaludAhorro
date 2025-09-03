from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.views.generic import ListView
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from .models import Usuario
from .forms import UsuarioForm


class UsuarioListView(ListView):
    model = Usuario
    template_name = "mantenimiento_usuarios/lista.html"
    context_object_name = "usuarios"


@require_http_methods(["GET", "POST"])
def usuario_create_modal(request):
    if request.method == "GET":
        html = render_to_string(
            "mantenimiento_usuarios/partials/_form.html",
            {"form": UsuarioForm(), "titulo": "Nuevo Usuario", "action": request.path},
            request=request,
        )
        return HttpResponse(html)

    form = UsuarioForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({"ok": True})
    html = render_to_string(
        "mantenimiento_usuarios/partials/_form.html",
        {"form": form, "titulo": "Nuevo Usuario", "action": request.path},
        request=request,
    )
    return JsonResponse({"ok": False, "html": html}, status=400)


@require_http_methods(["GET", "POST"])
def usuario_update_modal(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == "GET":
        html = render_to_string(
            "mantenimiento_usuarios/partials/_form.html",
            {"form": UsuarioForm(instance=usuario), "titulo": "Editar Usuario", "action": request.path},
            request=request,
        )
        return HttpResponse(html)

    form = UsuarioForm(request.POST, instance=usuario)
    if form.is_valid():
        form.save()
        return JsonResponse({"ok": True})
    html = render_to_string(
        "mantenimiento_usuarios/partials/_form.html",
        {"form": form, "titulo": "Editar Usuario", "action": request.path},
        request=request,
    )
    return JsonResponse({"ok": False, "html": html}, status=400)


@require_http_methods(["GET", "POST"])
def usuario_delete_modal(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == "GET":
        html = render_to_string(
            "mantenimiento_usuarios/partials/_confirm_delete.html",
            {"obj": usuario, "titulo": "Eliminar Usuario", "action": request.path},
            request=request,
        )
        return HttpResponse(html)

    # Borrado físico (si quieres baja lógica, cambia a: usuario.estado=False; usuario.save())
    usuario.delete()
    return JsonResponse({"ok": True})
