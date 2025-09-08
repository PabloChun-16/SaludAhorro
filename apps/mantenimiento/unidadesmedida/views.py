from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from apps.mantenimiento.models import Unidades_Medida
from .forms import UnidadesMedidaForm


def unidades_list(request):
    qs = Unidades_Medida.objects.order_by("nombre_unidad")
    return render(request, "unidadesmedida/lista.html", {"unidades": qs})


def unidades_create(request):
    form = UnidadesMedidaForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return JsonResponse({"ok": True})
        html = render_to_string(
            "unidadesmedida/partials/_form.html",
            {"form": form, "titulo": "Nueva Unidad de Medida", "action": request.path},
            request=request,
        )
        return JsonResponse({"ok": False, "html": html}, status=400)

    html = render_to_string(
        "unidadesmedida/partials/_form.html",
        {"form": form, "titulo": "Nueva Unidad de Medida", "action": request.path},
        request=request,
    )
    return HttpResponse(html)


def unidades_edit(request, pk):
    unidad = get_object_or_404(Unidades_Medida, pk=pk)
    form = UnidadesMedidaForm(request.POST or None, instance=unidad)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return JsonResponse({"ok": True})
        html = render_to_string(
            "unidadesmedida/partials/_form.html",
            {"form": form, "titulo": "Editar Unidad de Medida", "action": request.path},
            request=request,
        )
        return JsonResponse({"ok": False, "html": html}, status=400)

    html = render_to_string(
        "unidadesmedida/partials/_form.html",
        {"form": form, "titulo": "Editar Unidad de Medida", "action": request.path},
        request=request,
    )
    return HttpResponse(html)


def unidades_detail(request, pk):
    unidad = get_object_or_404(Unidades_Medida, pk=pk)
    html = render_to_string(
        "unidadesmedida/partials/_consultar.html",
        {"unidad": unidad, "titulo": "Detalle de Unidad de Medida"},
        request=request,
    )
    return HttpResponse(html)


def unidades_delete(request, pk):
    unidad = get_object_or_404(Unidades_Medida, pk=pk)

    if request.method == "POST":
        unidad.delete()
        return JsonResponse({"ok": True})

    html = render_to_string(
        "unidadesmedida/partials/_confirm_delete.html",
        {"unidad": unidad, "titulo": "Eliminar Unidad de Medida", "action": request.path},
        request=request,
    )
    return HttpResponse(html)
