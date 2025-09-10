from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from apps.mantenimiento.models import Condiciones_Almacenamiento
from .forms import CondicionesAlmacenamientoForm


def condiciones_list(request):
    """
    Vista que muestra la lista de todas las condiciones de almacenamiento.
    """
    qs = Condiciones_Almacenamiento.objects.order_by("nombre_condicion")
    return render(request, "condicionesalmacenamiento/lista.html", {"condiciones": qs})


def condiciones_create(request):
    """
    Vista para crear una nueva condición de almacenamiento.
    """
    form = CondicionesAlmacenamientoForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return JsonResponse({"ok": True})
        html = render_to_string(
            "condicionesalmacenamiento/partials/_form.html",
            {"form": form, "titulo": "Nueva Condición de Almacenamiento", "action": request.path},
            request=request,
        )
        return JsonResponse({"ok": False, "html": html}, status=400)

    html = render_to_string(
        "condicionesalmacenamiento/partials/_form.html",
        {"form": form, "titulo": "Nueva Condición de Almacenamiento", "action": request.path},
        request=request,
    )
    return HttpResponse(html)


def condiciones_edit(request, pk):
    """
    Vista para editar una condición de almacenamiento existente.
    """
    condicion = get_object_or_404(Condiciones_Almacenamiento, pk=pk)
    form = CondicionesAlmacenamientoForm(request.POST or None, instance=condicion)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return JsonResponse({"ok": True})
        html = render_to_string(
            "condicionesalmacenamiento/partials/_form.html",
            {"form": form, "titulo": "Editar Condición de Almacenamiento", "action": request.path},
            request=request,
        )
        return JsonResponse({"ok": False, "html": html}, status=400)

    html = render_to_string(
        "condicionesalmacenamiento/partials/_form.html",
        {"form": form, "titulo": "Editar Condición de Almacenamiento", "action": request.path},
        request=request,
    )
    return HttpResponse(html)


def condiciones_detail(request, pk):
    """
    Vista para ver el detalle de una condición de almacenamiento.
    """
    condicion = get_object_or_404(Condiciones_Almacenamiento, pk=pk)
    html = render_to_string(
        "condicionesalmacenamiento/partials/_consultar.html",
        {"condicion": condicion, "titulo": "Detalle de Condición de Almacenamiento"},
        request=request,
    )
    return HttpResponse(html)


def condiciones_delete(request, pk):
    """
    Vista para eliminar una condición de almacenamiento.
    """
    condicion = get_object_or_404(Condiciones_Almacenamiento, pk=pk)

    if request.method == "POST":
        condicion.delete()
        return JsonResponse({"ok": True})

    html = render_to_string(
        "condicionesalmacenamiento/partials/_confirm_delete.html",
        {"condicion": condicion, "titulo": "Eliminar Condición de Almacenamiento", "action": request.path},
        request=request,
    )
    return HttpResponse(html)