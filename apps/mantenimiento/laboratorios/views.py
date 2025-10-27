from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.template.loader import render_to_string
from apps.mantenimiento.models import Laboratorio
from .forms import LaboratorioForm

from django.utils.decorators import method_decorator
from apps.mantenimiento.decorators import solo_admin

def _is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


# LISTA
@solo_admin
def lista_laboratorios(request):
    laboratorios = Laboratorio.objects.order_by("nombre_laboratorio")
    return render(
        request,
        "mantenimiento_laboratorios/lista.html",
        {"laboratorios": laboratorios},
    )


# CREAR (contrato JSON => {"ok": true})
@solo_admin
def crear_laboratorio(request):
    if not _is_ajax(request):
        return HttpResponseBadRequest("Solo AJAX")

    form = LaboratorioForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return JsonResponse({"ok": True})
        # POST inválido -> devolver el parcial con errores
        html = render_to_string(
            "mantenimiento_laboratorios/partials/_form.html",
            {"form": form, "titulo": "Crear Laboratorio", "action": request.path},
            request=request,
        )
        return JsonResponse({"ok": False, "html": html}, status=400)

    # GET -> devolver el parcial vacío
    html = render_to_string(
        "mantenimiento_laboratorios/partials/_form.html",
        {"form": form, "titulo": "Crear Laboratorio", "action": request.path},
        request=request,
    )
    return HttpResponse(html)


# CONSULTAR (solo HTML)
@solo_admin
def consultar_laboratorio(request, pk):
    if not _is_ajax(request):
        return HttpResponseBadRequest("Solo AJAX")

    lab = get_object_or_404(Laboratorio, pk=pk)
    html = render_to_string(
        "mantenimiento_laboratorios/partials/_consultar.html",
        {"lab": lab, "titulo": "Detalle de Laboratorio"},
        request=request,
    )
    return HttpResponse(html)


# EDITAR (contrato JSON => {"ok": true})
@solo_admin
def editar_laboratorio(request, pk):
    if not _is_ajax(request):
        return HttpResponseBadRequest("Solo AJAX")

    lab = get_object_or_404(Laboratorio, pk=pk)
    form = LaboratorioForm(request.POST or None, instance=lab)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return JsonResponse({"ok": True})
        html = render_to_string(
            "mantenimiento_laboratorios/partials/_form.html",
            {"form": form, "titulo": "Editar Laboratorio", "action": request.path},
            request=request,
        )
        return JsonResponse({"ok": False, "html": html}, status=400)

    html = render_to_string(
        "mantenimiento_laboratorios/partials/_form.html",
        {"form": form, "titulo": "Editar Laboratorio", "action": request.path},
        request=request,
    )
    return HttpResponse(html)


# ELIMINAR (contrato JSON => {"ok": true})
@solo_admin
def eliminar_laboratorio(request, pk):
    if not _is_ajax(request):
        return HttpResponseBadRequest("Solo AJAX")

    lab = get_object_or_404(Laboratorio, pk=pk)

    if request.method == "POST":
        lab.delete()
        return JsonResponse({"ok": True})

    # GET -> confirmar
    html = render_to_string(
        "mantenimiento_laboratorios/partials/_confirm_delete.html",
        {"lab": lab, "titulo": "Eliminar Laboratorio", "action": request.path},
        request=request,
    )
    return HttpResponse(html)
