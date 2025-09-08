<<<<<<< HEAD
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from apps.mantenimiento.models import Laboratorio
from .forms import LaboratorioForm


# Listado de laboratorios
def lista_laboratorios(request):
    laboratorios = Laboratorio.objects.all().order_by("nombre_laboratorio")
    return render(
        request,
        "mantenimiento_laboratorios/lista.html",
        {"laboratorios": laboratorios}
    )

# Crear laboratorio
def crear_laboratorio(request):
    form = LaboratorioForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return JsonResponse({"success": True})

    # Si es GET o POST inválido, devolver HTML para el modal
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "mantenimiento_laboratorios/partials/_form.html",
            {"form": form, "titulo": "Crear Laboratorio", "action": request.path},
            request=request
        )
        return HttpResponse(html)

    return redirect("laboratorios:lista")

# Consultar laboratorio
def consultar_laboratorio(request, pk):
    lab = get_object_or_404(Laboratorio, pk=pk)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "mantenimiento_laboratorios/partials/_consultar.html",
            {"lab": lab},
            request=request
        )
        return HttpResponse(html)
    return redirect("laboratorios:lista")


# Editar laboratorio
def editar_laboratorio(request, pk):
    lab = get_object_or_404(Laboratorio, pk=pk)
    form = LaboratorioForm(request.POST or None, instance=lab)
    if request.method == "POST" and form.is_valid():
        form.save()
        return JsonResponse({"success": True})

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "mantenimiento_laboratorios/partials/_form.html",
            {"form": form, "titulo": "Editar Laboratorio", "action": request.path},
            request=request
        )
        return HttpResponse(html)

    return redirect("laboratorios:lista")


# Eliminar laboratorio
def eliminar_laboratorio(request, pk):
    lab = get_object_or_404(Laboratorio, pk=pk)
    if request.method == "POST":
        lab.delete()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "mantenimiento_laboratorios/partials/_confirm_delete.html",
            {"lab": lab},
            request=request
        )
        return HttpResponse(html)

    return redirect("laboratorios:lista")
=======
from django.views.generic import TemplateView, ListView
from apps.mantenimiento.models import Laboratorios

class IndexView(TemplateView):
    template_name = "mantenimiento/laboratorios/index.html"

class LaboratorioListView(ListView):
    model = Laboratorios
    template_name = "mantenimiento_laboratorios/lista.html"
    context_object_name = "items"
    paginate_by = 20
>>>>>>> 8f1bf632157c62fc82b9665437497b376869f702
