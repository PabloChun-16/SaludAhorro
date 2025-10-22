from urllib import request
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from apps.mantenimiento.models import Estado_Producto
from apps.inventario.models import Productos
from .forms import ProductoForm

from itertools import chain
from apps.salidas_devoluciones.models import Movimientos_Inventario_Sucursal
from apps.ajustes_inventario.models import Detalle_Conteo
from django.db.models import F, Value, Case, When, IntegerField, CharField
from django.utils.dateparse import parse_date
from django.utils.timezone import is_aware, make_naive, make_aware, get_current_timezone

from django.db.models import F, Value, Case, When, IntegerField, CharField, ExpressionWrapper
from django.db.models.functions import Abs
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

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

# Activar
@require_http_methods(["GET", "POST"])
def activar_producto(request, pk):
    producto = get_object_or_404(Productos, pk=pk)

    if request.method == "POST":
        try:
            estado_activo = Estado_Producto.objects.get(nombre_estado="Activo")
            # idempotente: si ya está activo, igual devolvemos ok
            if producto.id_estado_producto_id == estado_activo.id:
                return JsonResponse({"success": True, "message": "El producto ya estaba activo"})
            producto.id_estado_producto = estado_activo
            producto.save(update_fields=["id_estado_producto"])
            return JsonResponse({"success": True})
        except Estado_Producto.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Estado 'Activo' no existe"},
                status=500
            )

    # GET: render del modal de confirmación
    html = render_to_string(
        "productos/partials/_confirm_activar.html",
        {"producto": producto, "action": request.path},
        request=request,
    )
    return HttpResponse(html)


# ---------------------------------------------------------------
# MODAL DE FECHAS (PASO 1)
# ---------------------------------------------------------------
@require_http_methods(["GET"])
def kardex_modal(request, pk):
    producto = get_object_or_404(Productos, pk=pk)
    html = render_to_string(
        "productos/partials/_kardex_fechas.html",
        {
            "producto": producto,
            "action": f"/inventario/productos/{pk}/kardex/resultado/",  # ✅ ruta correcta
        },
        request=request,
    )
    return HttpResponse(html)


def obtener_kardex_data(producto, fecha_inicio, fecha_fin):
    """Devuelve los movimientos del kardex con su saldo calculado"""
    from datetime import datetime, time
    from itertools import chain
    from django.utils.timezone import is_aware, make_naive, get_current_timezone
    from django.db.models.functions import Cast

    tz = get_current_timezone()

    # 🔹 Movimientos normales
    movimientos = (
        Movimientos_Inventario_Sucursal.objects
        .filter(
            fecha_hora__range=[fecha_inicio, fecha_fin],
            id_lote__id_producto=producto,
        )
        .select_related("id_tipo_movimiento", "id_lote")
        .annotate(
            naturaleza_int=Cast(F("id_tipo_movimiento__naturaleza"), IntegerField()),
            fecha=F("fecha_hora"),
            tipo=F("id_tipo_movimiento__descripcion"),
            origen=Value("Movimiento", output_field=CharField()),
            cantidad_total=ExpressionWrapper(
                Case(
                    When(naturaleza_int=1, then=F("cantidad")),
                    When(naturaleza_int=-1, then=F("cantidad") * Value(-1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                output_field=IntegerField(),
            ),
            entrada=Case(
                When(naturaleza_int=1, then=F("cantidad")),
                default=Value(0),
                output_field=IntegerField()
            ),
            salida=Case(
                When(naturaleza_int=-1, then=F("cantidad")),
                default=Value(0),
                output_field=IntegerField()
            ),
        )
        .values("fecha", "tipo", "origen", "cantidad_total", "entrada", "salida")
    )

    # 🔹 Ajustes físicos
    ajustes = (
        Detalle_Conteo.objects
        .filter(
            id_conteo__estado="Completado",
            id_conteo__fecha_conteo__range=[fecha_inicio.date(), fecha_fin.date()],
            id_lote__id_producto=producto,
        )
        .select_related("id_conteo", "id_lote")
        .annotate(
            fecha=F("id_conteo__fecha_conteo"),
            tipo=F("id_conteo__tipo_ajuste"),
            origen=Value("Ajuste Físico", output_field=CharField()),
            cantidad_total=F("diferencia"),
            entrada=Case(
                When(diferencia__gt=0, then=F("diferencia")),
                default=Value(0),
                output_field=IntegerField()
            ),
            salida=Case(
                When(diferencia__lt=0, then=Abs(F("diferencia"))),
                default=Value(0),
                output_field=IntegerField()
            ),
        )
        .values("fecha", "tipo", "origen", "cantidad_total", "entrada", "salida")
    )

    def normalizar_fecha(f):
        if isinstance(f, datetime):
            dt = f
        else:
            dt = datetime.combine(f, time.max)
        if is_aware(dt):
            dt = make_naive(dt, tz)
        return dt

    kardex_data = sorted(chain(movimientos, ajustes), key=lambda x: normalizar_fecha(x["fecha"]))

    # 🔹 Calcular saldo acumulado
    saldo = 0
    for k in kardex_data:
        cantidad = int(k.get("cantidad_total") or 0)
        if k["tipo"].lower().startswith(("venta", "salida")):
            cantidad = -abs(cantidad)
        elif k["tipo"].lower().startswith(("recepción", "ingreso", "devolución")):
            cantidad = abs(cantidad)
        saldo += cantidad
        k["saldo"] = saldo

    return kardex_data


# ---------------------------------------------------------------
# RESULTADO DEL KARDEX (PASO 2)
# ---------------------------------------------------------------
def kardex_resultado(request, pk):
    from datetime import datetime, time
    from django.utils.timezone import make_aware, get_current_timezone
    from django.utils.dateparse import parse_date

    producto = get_object_or_404(Productos, pk=pk)
    fecha_inicio = parse_date(request.GET.get("fecha_inicio"))
    fecha_fin = parse_date(request.GET.get("fecha_fin"))

    tz = get_current_timezone()
    fecha_inicio = make_aware(datetime.combine(fecha_inicio, time.min), tz)
    fecha_fin = make_aware(datetime.combine(fecha_fin, time.max), tz)

    kardex_data = obtener_kardex_data(producto, fecha_inicio, fecha_fin)

    html = render_to_string(
        "productos/partials/_kardex_resultado.html",
        {
            "producto": producto,
            "kardex": kardex_data,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
        },
        request=request,
    )
    return HttpResponse(html)


def kardex_exportar(request, pk):
    producto = get_object_or_404(Productos, pk=pk)
    fecha_inicio = parse_date(request.GET.get("fecha_inicio"))
    fecha_fin = parse_date(request.GET.get("fecha_fin"))

    from datetime import datetime, time
    from django.utils.timezone import make_aware, get_current_timezone
    tz = get_current_timezone()
    fecha_inicio = make_aware(datetime.combine(fecha_inicio, time.min), tz)
    fecha_fin = make_aware(datetime.combine(fecha_fin, time.max), tz)

    kardex_data = obtener_kardex_data(producto, fecha_inicio, fecha_fin)

    # Generar PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph(f"Kardex de {producto.nombre}", styles["Title"])
    elements += [title, Spacer(1, 12), Paragraph(f"Desde {fecha_inicio.date()} hasta {fecha_fin.date()}", styles["Normal"]), Spacer(1, 12)]

    data = [["Fecha", "Tipo", "Origen", "Entrada", "Salida", "Saldo"]]
    for k in kardex_data:
        data.append([
            k["fecha"].strftime("%d/%m/%Y"),
            k["tipo"], k["origen"],
            str(k["entrada"]), str(k["salida"]), str(k["saldo"])
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f7fa")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (3, 1), (-1, -1), "CENTER"),
    ]))

    elements.append(table)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Kardex_{producto.nombre}.pdf"'
    response.write(pdf)
    return response
