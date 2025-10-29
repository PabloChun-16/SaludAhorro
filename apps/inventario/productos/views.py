from urllib import request
from datetime import datetime, time

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from apps.mantenimiento.models import Estado_Producto
from apps.inventario.models import Productos, Lotes
from .forms import ProductoForm

from itertools import chain
from apps.salidas_devoluciones.models import Movimientos_Inventario_Sucursal
from apps.ajustes_inventario.models import Detalle_Conteo
from django.db.models import F, Value, Case, When, IntegerField, CharField
from django.utils.dateparse import parse_date
from django.utils.timezone import (
    is_aware,
    make_naive,
    make_aware,
    get_current_timezone,
    localdate,
)

from django.db.models import F, Value, Case, When, IntegerField, CharField, ExpressionWrapper
from django.db.models.functions import Abs, Cast
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from django.db.models import Sum  


# Listado
def productos_list(request):
    productos = Productos.objects.all().order_by("nombre")
    laboratorios = (
        Productos.objects.filter(id_laboratorio__isnull=False)
        .order_by("id_laboratorio__nombre_laboratorio")
        .values_list("id_laboratorio__nombre_laboratorio", flat=True)
        .distinct()
    )
    presentaciones = (
        Productos.objects.filter(id_presentacion__isnull=False)
        .order_by("id_presentacion__nombre_presentacion")
        .values_list("id_presentacion__nombre_presentacion", flat=True)
        .distinct()
    )
    return render(
        request,
        "productos/lista.html",
        {
            "productos": productos,
            "laboratorios": laboratorios,
            "presentaciones": presentaciones,
        },
    )


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


@require_http_methods(["GET", "POST"])
def inactivar_producto(request, pk):
    """
    Reglas:
      - Si ya está Inactivo -> OK (idempotente).
      - Bloquear si hay stock disponible en cualquier lote.
    """
    producto = get_object_or_404(Productos, pk=pk)

    if request.method == "POST":
        try:
            inactivo = Estado_Producto.objects.get(nombre_estado="Inactivo")
        except Estado_Producto.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Estado 'Inactivo' no existe."}, status=500
            )

        # Idempotente
        if producto.id_estado_producto_id == inactivo.id:
            return JsonResponse({"success": True, "message": "El producto ya estaba inactivo."})

        # Validación de stock
        tot = (
            Lotes.objects.filter(id_producto=producto, cantidad_disponible__gt=0)
            .aggregate(total=Sum("cantidad_disponible"))
            .get("total") or 0
        )
        if tot > 0:
            lotes = list(
                Lotes.objects.filter(id_producto=producto, cantidad_disponible__gt=0)
                .values("numero_lote", "cantidad_disponible")
                .order_by("-cantidad_disponible")[:10]
            )
            return JsonResponse(
                {
                    "success": False,
                    "error": "No se puede inactivar. El producto aún tiene stock disponible.",
                    "total": int(tot),
                    "lotes": [{"numero_lote": l["numero_lote"], "cantidad": int(l["cantidad_disponible"])} for l in lotes],
                },
                status=400,
            )

        # Cambiar estado
        producto.id_estado_producto = inactivo
        producto.save(update_fields=["id_estado_producto"])
        return JsonResponse({"success": True})

    # GET -> modal de confirmación
    html = render_to_string(
        "productos/partials/_confirm_inactivar.html",
        {"producto": producto, "action": request.path},
        request=request,
    )
    return HttpResponse(html)


@require_http_methods(["GET", "POST"])
def activar_producto(request, pk):
    """
    Reglas:
      - Si ya está Activo -> OK (idempotente).
      - (Opcional) Validar datos mínimos del maestro antes de activar.
    """
    producto = get_object_or_404(Productos, pk=pk)

    if request.method == "POST":
        try:
            activo = Estado_Producto.objects.get(nombre_estado="Activo")
        except Estado_Producto.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Estado 'Activo' no existe."}, status=500
            )

        # Idempotente
        if producto.id_estado_producto_id == activo.id:
            return JsonResponse({"success": True, "message": "El producto ya estaba activo."})

        # (Opcional) Validación de maestro mínimo
        faltantes = []
        if not producto.id_unidad_medida_id:
            faltantes.append("Unidad de medida")
        if not producto.id_presentacion_id:
            faltantes.append("Presentación")
        if not producto.id_laboratorio_id:
            faltantes.append("Laboratorio")
        if faltantes:
            return JsonResponse(
                {
                    "success": False,
                    "error": "No se puede activar: faltan datos mínimos -> " + ", ".join(faltantes),
                },
                status=400,
            )

        # Activar
        producto.id_estado_producto = activo
        producto.save(update_fields=["id_estado_producto"])
        return JsonResponse({"success": True})

    # GET -> modal de confirmación
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


def _resolver_rango_fechas(request):
    """
    Normaliza los parámetros de fecha recibidos vía GET.
    Si uno de los extremos viene vacío se reutiliza el otro, y si ambos vienen
    vacíos se usa la fecha actual. El resultado siempre es consciente de zona.
    """
    fecha_inicio_raw = request.GET.get("fecha_inicio")
    fecha_fin_raw = request.GET.get("fecha_fin")

    fecha_inicio = parse_date(fecha_inicio_raw) if fecha_inicio_raw else None
    fecha_fin = parse_date(fecha_fin_raw) if fecha_fin_raw else None

    hoy = localdate()
    if fecha_inicio is None and fecha_fin is None:
        fecha_inicio = fecha_fin = hoy
    elif fecha_inicio is None:
        fecha_inicio = fecha_fin or hoy
    elif fecha_fin is None:
        fecha_fin = fecha_inicio

    if fecha_inicio > fecha_fin:
        fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

    tz = get_current_timezone()
    fecha_inicio_dt = make_aware(datetime.combine(fecha_inicio, time.min), tz)
    fecha_fin_dt = make_aware(datetime.combine(fecha_fin, time.max), tz)
    return fecha_inicio_dt, fecha_fin_dt


def obtener_kardex_data(producto, fecha_inicio, fecha_fin):
    """Devuelve los movimientos del kardex con su saldo calculado"""
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
    producto = get_object_or_404(Productos, pk=pk)
    fecha_inicio, fecha_fin = _resolver_rango_fechas(request)

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
    fecha_inicio, fecha_fin = _resolver_rango_fechas(request)

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
