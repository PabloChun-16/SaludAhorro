from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from apps.mantenimiento.models import Estado_Producto
from apps.inventario.models import Productos
from .forms import ProductoForm


# Listado
def productos_list(request):
    productos = Productos.objects.all().order_by("nombre")
    return render(request, "productos/lista.html", {"productos": productos})


# Crear
@require_http_methods(["GET", "POST"])
def productos_create(request):
    form = ProductoForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return JsonResponse({"ok": True})
        html = render_to_string(
            "productos/partials/_form.html",
            {"form": form, "titulo": "Nuevo Producto", "action": request.path},
            request=request,
        )
        return JsonResponse({"ok": False, "html": html}, status=400)

    html = render_to_string(
        "productos/partials/_form.html",
        {"form": form, "titulo": "Nuevo Producto", "action": request.path},
        request=request,
    )
    return HttpResponse(html)


# Detalle
@require_http_methods(["GET"])
def productos_detail(request, pk):
    producto = get_object_or_404(Productos, pk=pk)
    html = render_to_string(
        "productos/partials/_consultar.html",
        {"producto": producto, "titulo": "Detalle del Producto"},
        request=request,
    )
    return HttpResponse(html)


# Editar
@require_http_methods(["GET", "POST"])
def productos_edit(request, pk):
    producto = get_object_or_404(Productos, pk=pk)
    form = ProductoForm(request.POST or None, request.FILES or None, instance=producto)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return JsonResponse({"ok": True})
        html = render_to_string(
            "productos/partials/_form.html",
            {"form": form, "titulo": "Editar Producto", "action": request.path},
            request=request,
        )
        return JsonResponse({"ok": False, "html": html}, status=400)

    html = render_to_string(
        "productos/partials/_form.html",
        {"form": form, "titulo": "Editar Producto", "action": request.path},
        request=request,
    )
    return HttpResponse(html)


# Inactivar
@require_http_methods(["GET", "POST"])
def inactivar_producto(request, pk):
    producto = get_object_or_404(Productos, pk=pk)

    if request.method == "POST":
        try:
            inactivo = Estado_Producto.objects.get(nombre_estado="Inactivo")
            producto.id_estado_producto = inactivo
            producto.save()
            return JsonResponse({"success": True})
        except Estado_Producto.DoesNotExist:
            return JsonResponse({"success": False, "error": "Estado 'Inactivo' no encontrado."}, status=500)

    html = render_to_string(
        "productos/partials/_confirm_inactivar.html",  # cambiamos nombre del template
        {"producto": producto, "action": request.path},
        request=request,
    )
    return HttpResponse(html)

#Activar
def activar_producto(request, pk):
    producto = get_object_or_404(Productos, pk=pk)

    try:
        estado_activo = Estado_Producto.objects.get(nombre_estado="Activo")
        producto.id_estado_producto = estado_activo
        producto.save()
        return JsonResponse({"success": True})
    except Estado_Producto.DoesNotExist:
        return JsonResponse({"success": False, "error": "Estado 'Activo' no existe"}, status=500)