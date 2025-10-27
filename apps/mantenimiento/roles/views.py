# apps/mantenimiento/roles/views.py
from django import forms
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.generic import ListView
from apps.mantenimiento.models import Roles

from django.utils.decorators import method_decorator
from apps.mantenimiento.decorators import solo_admin

@method_decorator(solo_admin, name='dispatch')
class RolListView(ListView):
    model = Roles
    template_name = "mantenimiento_roles/lista.html"
    context_object_name = "roles"
    paginate_by = 20


class RolForm(forms.ModelForm):
    class Meta:
        model = Roles
        fields = ["nombre_rol"]
        widgets = {
            "nombre_rol": forms.TextInput(attrs={
                "class": "form-control",
            })
        }


def _is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@solo_admin
# ====== CREAR ======
def rol_crear(request):
    if not _is_ajax(request):
        return HttpResponseBadRequest("Solo AJAX")

    if request.method == "GET":
        form = RolForm()
        html = render_to_string(
            "mantenimiento_roles/partials/_form.html",
            {"form": form, "titulo": "Nuevo Rol", "action": request.path},
            request=request,
        )
        return HttpResponse(html)

    # POST
    form = RolForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({"ok": True})

    html = render_to_string(
        "mantenimiento_roles/partials/_form.html",
        {"form": form, "titulo": "Nuevo Rol", "action": request.path},
        request=request,
    )
    return JsonResponse({"ok": False, "html": html}, status=400)


@solo_admin
# ====== CONSULTAR ======
def rol_consultar(request, pk):
    if not _is_ajax(request):
        return HttpResponseBadRequest("Solo AJAX")

    rol = get_object_or_404(Roles, pk=pk)
    html = render_to_string(
        "mantenimiento_roles/partials/_consultar.html",
        {"rol": rol, "titulo": "Detalle de Rol"},
        request=request,
    )
    return HttpResponse(html)


@solo_admin
# ====== EDITAR ======
def rol_editar(request, pk):
    if not _is_ajax(request):
        return HttpResponseBadRequest("Solo AJAX")

    rol = get_object_or_404(Roles, pk=pk)

    if request.method == "GET":
        form = RolForm(instance=rol)
        html = render_to_string(
            "mantenimiento_roles/partials/_form.html",
            {"form": form, "titulo": "Editar Rol", "action": request.path},
            request=request,
        )
        return HttpResponse(html)

    # POST
    form = RolForm(request.POST, instance=rol)
    if form.is_valid():
        form.save()
        return JsonResponse({"ok": True})

    html = render_to_string(
        "mantenimiento_roles/partials/_form.html",
        {"form": form, "titulo": "Editar Rol", "action": request.path},
        request=request,
    )
    return JsonResponse({"ok": False, "html": html}, status=400)


@solo_admin
# ====== ELIMINAR ======
def rol_eliminar(request, pk):
    if not _is_ajax(request):
        return HttpResponseBadRequest("Solo AJAX")

    rol = get_object_or_404(Roles, pk=pk)

    if request.method == "GET":
        html = render_to_string(
            "mantenimiento_roles/partials/_confirm_delete.html",
            {"rol": rol, "titulo": "Eliminar Rol", "action": request.path},
            request=request,
        )
        return HttpResponse(html)

    # POST (confirmación)
    rol.delete()
    return JsonResponse({"ok": True})
