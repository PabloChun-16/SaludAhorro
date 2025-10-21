from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from apps.mantenimiento.models import Presentaciones
from .forms import PresentacionForm
from django.views.decorators.http import require_http_methods
from django.urls import reverse


# Listado de presentaciones
def lista_presentaciones(request):
    presentaciones = Presentaciones.objects.all().order_by("nombre_presentacion")
    return render(
        request,
        "mantenimiento_presentaciones/lista.html",
        {"presentaciones": presentaciones}
    )


# Crear presentación
@require_http_methods(["GET", "POST"])
def crear_presentacion(request):
    form = PresentacionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return JsonResponse({"success": True})

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "mantenimiento_presentaciones/partials/_form.html",
            {"form": form, "titulo": "Crear Presentación", "action": request.path},
            request=request
        )
        return HttpResponse(html)

    return redirect("mantenimiento_presentaciones:lista")


# Consultar presentación
@require_http_methods(["GET"])
def consultar_presentacion(request, pk):
    presentacion = get_object_or_404(Presentaciones, pk=pk)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "mantenimiento_presentaciones/partials/_consultar.html",
            {"presentacion": presentacion},
            request=request
        )
        return HttpResponse(html)
    return redirect("mantenimiento_presentaciones:lista")


# Editar presentación
@require_http_methods(["GET", "POST"])
def editar_presentacion(request, pk):
    presentacion = get_object_or_404(Presentaciones, pk=pk)
    form = PresentacionForm(request.POST or None, instance=presentacion)
    if request.method == "POST" and form.is_valid():
        form.save()
        return JsonResponse({"success": True})

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "mantenimiento_presentaciones/partials/_form.html",
            {"form": form, "titulo": "Editar Presentación", "action": request.path},
            request=request
        )
        return HttpResponse(html)

    return redirect("mantenimiento_presentaciones:lista")


# La función para eliminar un registro
@require_http_methods(["GET", "POST"])
def eliminar_presentacion(request, pk):
    presentacion = get_object_or_404(Presentaciones, pk=pk)

    if request.method == "POST":
        try:
            presentacion.delete()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    # GET: renderiza el modal de confirmación
    html = render_to_string(
        "mantenimiento_presentaciones/partials/_confirm_delete.html",
        {
            "presentacion": presentacion,
            "action": reverse("mantenimiento:mantenimiento_presentaciones:eliminar", args=[pk]),  # 🔹 aquí defines la acción
        },
        request=request
    )
    return HttpResponse(html)