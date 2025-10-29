import json
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from apps.mantenimiento.models import (
    Tipo_Movimiento_Inventario,
    Estado_Movimiento_Inventario,
)

from apps.inventario.models import Productos, Lotes
from apps.salidas_devoluciones.models import Movimientos_Inventario_Sucursal
from django.views.decorators.http import require_POST
from django.db.models import Max, Sum, F, Subquery, OuterRef

from django.http import HttpResponse
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


@login_required
@require_POST
@transaction.atomic
def devolucion_cancel(request, ref: str):
    """
    Cancela TODOS los movimientos DEV 'Completado' de la referencia dada.
    - Valida que exista al menos un DEV completado y que no esté ya totalmente cancelada.
    - Verifica que haya stock suficiente para revertir cada renglón (no dejar lotes en negativo).
    - Descuenta del inventario (resta lo devuelto).
    - Marca los DEV originales como 'Cancelado'.
    - Crea un movimiento DEV con cantidad NEGATIVA por cada renglón revertido (auditoría).
    """
    # Estados
    try:
        estado_ok = Estado_Movimiento_Inventario.objects.get(nombre_estado="Completado")
        estado_cancel = Estado_Movimiento_Inventario.objects.get(nombre_estado="Cancelado")
    except Estado_Movimiento_Inventario.DoesNotExist:
        return JsonResponse({"success": False, "errors": "Estados 'Completado/Cancelado' no configurados."}, status=400)

    # Tipo DEV
    try:
        tipo_dev = Tipo_Movimiento_Inventario.objects.get(codigo="DEV")
    except Tipo_Movimiento_Inventario.DoesNotExist:
        return JsonResponse({"success": False, "errors": "No existe el tipo de movimiento 'DEV'."}, status=400)

    # Movimientos DEV de esta referencia
    devs = (
        Movimientos_Inventario_Sucursal.objects
        .select_for_update()
        .select_related("id_lote")
        .filter(id_tipo_movimiento=tipo_dev, referencia_transaccion=ref)
        .order_by("id")
    )
    if not devs.exists():
        return JsonResponse({"success": False, "errors": "No hay devoluciones registradas para esta referencia."}, status=404)

    # ¿Ya están todos cancelados?
    hay_completados = devs.filter(estado_movimiento_inventario=estado_ok).exists()
    if not hay_completados:
        return JsonResponse({"success": False, "errors": "La devolución ya está cancelada."}, status=400)

    # Agrupa por lote la cantidad a revertir (solo los completados, que suman stock)
    a_revertir = {}  # lote_id -> cantidad_total
    for m in devs.filter(estado_movimiento_inventario=estado_ok):
        qty = int(m.cantidad or 0)
        if qty <= 0:
            # Un DEV negativo no suma stock (p. ej., ajustes previos); lo saltamos
            continue
        a_revertir[m.id_lote_id] = a_revertir.get(m.id_lote_id, 0) + qty

    if not a_revertir:
        return JsonResponse({"success": False, "errors": "No hay renglones revertibles en estado 'Completado'."}, status=400)

    # Validar stock suficiente para revertir (no dejar lotes en negativo)
    lotes = {l.id: l for l in Lotes.objects.select_for_update().filter(id__in=a_revertir.keys())}
    faltantes = []
    for lote_id, qty in a_revertir.items():
        lote = lotes.get(lote_id)
        disp = int(lote.cantidad_disponible or 0)
        if disp < qty:
            faltantes.append(f"Lote {lote.numero_lote}: disponible {disp}, a revertir {qty}.")

    if faltantes:
        return JsonResponse({
            "success": False,
            "errors": ["Stock insuficiente para revertir la devolución en:"] + faltantes
        }, status=400)

    # Aplicar reverso por cada renglón completado
    usuario = request.user
    for m in devs.filter(estado_movimiento_inventario=estado_ok):
        qty = int(m.cantidad or 0)
        if qty <= 0:
            continue  # solo revertimos los DEV positivos

        # 1) Descontar del lote
        Lotes.objects.filter(pk=m.id_lote_id).update(
            cantidad_disponible=F("cantidad_disponible") - qty
        )

        # 2) Marcar original como Cancelado
        m.estado_movimiento_inventario = estado_cancel
        m.save(update_fields=["estado_movimiento_inventario"])

        # 3) Asiento inverso (DEV negativo) para auditoría
        Movimientos_Inventario_Sucursal.objects.create(
            id_lote=m.id_lote,
            id_tipo_movimiento=tipo_dev,
            cantidad=-qty,
            id_usuario=usuario,
            referencia_transaccion=ref,
            comentario="Reversa por cancelación de devolución",
            estado_movimiento_inventario=estado_cancel,
        )

    return JsonResponse({"success": True})


# ============================================================
# LISTA
# ============================================================

@login_required
def devolucion_list(request):
    # 1) Ids del último movimiento DEV por referencia
    latest_ids = (
        Movimientos_Inventario_Sucursal.objects
        .filter(id_tipo_movimiento__codigo="DEV")
        .values('referencia_transaccion')
        .annotate(last_id=Max('id'))
        .values_list('last_id', flat=True)
    )

    # 2) Carga solo esos movimientos
    qs = (
        Movimientos_Inventario_Sucursal.objects
        .filter(id__in=latest_ids)
        .select_related("id_usuario", "estado_movimiento_inventario")
        .order_by('-fecha_hora')   # más recientes primero
    )

    devoluciones = [{
        "referencia_transaccion": m.referencia_transaccion,
        "fecha": m.fecha_hora,
        "usuario": m.id_usuario,
        "estado": m.estado_movimiento_inventario,
    } for m in qs]

    return render(request, "devoluciones/lista.html", {"devoluciones": devoluciones})


# ============================================================
# CONSULTAR
# ============================================================

@login_required
def devolucion_detail(request, ref: str):
    """
    Muestra el detalle de una devolución (todos los movimientos DEV
    con esa referencia de factura).
    """
    movimientos = (
        Movimientos_Inventario_Sucursal.objects
        .filter(id_tipo_movimiento__codigo="DEV", referencia_transaccion=ref)
        .select_related(
            "id_lote",
            "id_lote__id_producto",
            "id_usuario",
            "estado_movimiento_inventario",
        )
        .order_by("id")
    )

    header = movimientos.first()
    return render(
        request,
        "devoluciones/partials/_consultar.html",
        {
            "referencia": ref,
            "header": header,         # para fecha, usuario, estado, comentario
            "movimientos": movimientos,
        },
    )


# ============================================================
# CREAR
# ============================================================

@login_required
@transaction.atomic
def devolucion_create(request):
    """
    GET  -> devuelve el formulario parcial `devoluciones/form.html`
    POST -> guarda la devolución:
            - valida que el producto y lote existan y que estén asociados a la factura (VEN)
            - suma el stock al lote
            - registra un movimiento DEV positivo para cada renglón
    Espera payload JSON con:
      {
        "form_data": {
          "numero_factura": "...",
          "fecha_devolucion": "YYYY-MM-DDTHH:MM",   # opcional (el modelo usa auto_now_add)
          "motivo": "texto opcional"
        },
        "detalles": [
          {
            "producto_id": 123,
            "lote_id": 456,           # requerido (escogido por el usuario o sugerido)
            "cantidad": 3
          },
          ...
        ]
      }
    """
    if request.method == "GET":
        return render(
            request,
            "devoluciones/partials/form.html",
            {"now": timezone.localtime().strftime("%Y-%m-%dT%H:%M")},
        )

    # POST JSON
    try:
        data = json.loads((request.body or b"").decode("utf-8"))
    except Exception:
        return JsonResponse({"success": False, "errors": "Payload inválido."}, status=400)

    form_data = data.get("form_data", {}) or {}
    detalles = data.get("detalles", []) or []

    referencia = (form_data.get("numero_factura") or "").strip()
    motivo = (form_data.get("motivo") or "").strip()
    # fecha_devolucion = form_data.get("fecha_devolucion")  # tu modelo usa auto_now_add

    if not referencia:
        return JsonResponse({"success": False, "errors": "No. de factura requerido."}, status=400)
    if not detalles:
        return JsonResponse({"success": False, "errors": "Debe agregar al menos un producto."}, status=400)

    # Tipo y estado necesarios
    try:
        tipo_dev = Tipo_Movimiento_Inventario.objects.get(codigo="DEV")
    except Tipo_Movimiento_Inventario.DoesNotExist:
        return JsonResponse({"success": False, "errors": "No existe el tipo de movimiento 'DEV'."}, status=400)

    try:
        estado_ok = Estado_Movimiento_Inventario.objects.get(nombre_estado="Completado")
    except Estado_Movimiento_Inventario.DoesNotExist:
        return JsonResponse({"success": False, "errors": "No existe el estado de movimiento 'Completado'."}, status=400)

    usuario = request.user

    try:
        for idx, det in enumerate(detalles, start=1):
            pid = det.get("producto_id")
            lote_id = det.get("lote_id")
            qty = det.get("cantidad")

            try:
                qty = int(qty)
            except Exception:
                qty = 0

            if not pid or not lote_id or qty <= 0:
                raise ValueError(f"Dato faltante/erróneo en línea {idx}.")

            producto = get_object_or_404(Productos, pk=pid)
            lote = get_object_or_404(Lotes, pk=lote_id)

            # 1) Validar que el lote corresponda al producto
            if lote.id_producto_id != producto.id:
                raise ValueError(f"El lote seleccionado no pertenece al producto en línea {idx}.")

            # 2) Validar que en esa factura (ref) hubo una VENTA de ese producto (y de ese lote)
            vendidas_qs = (
                Movimientos_Inventario_Sucursal.objects
                .filter(
                    id_tipo_movimiento__codigo="VEN",
                    referencia_transaccion=referencia,
                    id_lote=lote,
                )
                .aggregate(total=Sum("cantidad"))
            )
            # En VEN la cantidad es NEGATIVA, por lo que total será <= 0 si existió.
            total_vendida = vendidas_qs["total"] or 0
            if total_vendida == 0:
                # No se vendió ese lote en esa factura
                raise ValueError(
                    f"El lote {lote.numero_lote} del producto '{producto.nombre}' no figura en la factura {referencia}."
                )

            # 3) Actualizar inventario (suma)
            Lotes.objects.filter(pk=lote.pk).update(
                cantidad_disponible=F("cantidad_disponible") + qty
            )
            lote.refresh_from_db(fields=["cantidad_disponible"])

            # 4) Registrar movimiento DEV (cantidad POSITIVA)
            Movimientos_Inventario_Sucursal.objects.create(
                id_lote=lote,
                id_tipo_movimiento=tipo_dev,
                cantidad=qty,
                id_usuario=usuario,
                referencia_transaccion=referencia,
                comentario=motivo or None,
                estado_movimiento_inventario=estado_ok,
                # fecha_hora -> auto_now_add del modelo
            )

        return JsonResponse({"success": True})

    except ValueError as e:
        transaction.set_rollback(True)
        return JsonResponse({"success": False, "errors": str(e)}, status=400)
    except Exception:
        transaction.set_rollback(True)
        return JsonResponse({"success": False, "errors": "Error interno al procesar la devolución."}, status=500)


# ============================================================
# ENDPOINT AUXILIAR: lotes vendidos en una factura para un producto
# ============================================================

@login_required
def lotes_vendidos_por_factura(request, ref: str, producto_id: int):
    """
    Devuelve la lista de lotes (y cantidades vendidas) que aparecen en la factura (VEN)
    para el producto dado. Sirve para autollenar/sugerir el campo *Lote* en el form de devolución.
    Respuesta: [
      {"id": 1, "numero_lote": "A-001", "fecha_caducidad": "2026-11-30", "vendido": 5, "disponible": 12},
      ...
    ]
    """
    producto = get_object_or_404(Productos, pk=producto_id)

    # Movimientos de venta por lote (las cantidades son negativas, hacemos ABS)
    ventas_por_lote = (
        Movimientos_Inventario_Sucursal.objects
        .filter(
            id_tipo_movimiento__codigo="VEN",
            referencia_transaccion=ref,
            id_lote__id_producto=producto,
        )
        .values("id_lote")                # agrupamos por lote
        .annotate(total_vendido=Sum("cantidad"))
    )

    # Carga los lotes involucrados
    lote_ids = [v["id_lote"] for v in ventas_por_lote]
    lotes = {l.id: l for l in Lotes.objects.filter(id__in=lote_ids)}

    results = []
    for row in ventas_por_lote:
        lote = lotes.get(row["id_lote"])
        if not lote:
            continue
        vendido_abs = abs(int(row["total_vendido"] or 0))
        results.append({
            "id": lote.id,
            "numero_lote": lote.numero_lote,
            "fecha_caducidad": (
                lote.fecha_caducidad.strftime("%Y-%m-%d") if lote.fecha_caducidad else ""
            ),
            "vendido": vendido_abs,
            "disponible": int(lote.cantidad_disponible or 0),
        })

    return JsonResponse(results, safe=False)

@login_required
def devolucion_export_pdf(request, ref: str):
    """
    Exporta el detalle de una devolución en formato PDF.
    """
    movimientos = (
        Movimientos_Inventario_Sucursal.objects
        .filter(id_tipo_movimiento__codigo="DEV", referencia_transaccion=ref)
        .select_related("id_lote", "id_lote__id_producto", "id_usuario", "estado_movimiento_inventario")
        .order_by("id")
    )

    if not movimientos.exists():
        return HttpResponse("No hay movimientos para esta devolución.", status=404)

    header = movimientos.first()

    # ---- Configuración del PDF ----
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="devolucion_{ref}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []

    # ---- Encabezado ----
    title_style = ParagraphStyle(
        "Titulo",
        parent=styles["Title"],
        fontSize=18,
        textColor=colors.HexColor("#0F7A3A"),
        alignment=1,  # centrado
    )
    elements.append(Paragraph(f"<b>Detalle de Devolución</b>", title_style))
    elements.append(Spacer(1, 12))

    info_style = ParagraphStyle("info", fontSize=11, leading=14, spaceAfter=4)
    info_data = [
        f"<b>No. Factura:</b> {ref}",
        f"<b>Fecha:</b> {header.fecha_hora.strftime('%d/%m/%Y %H:%M') if header.fecha_hora else '—'}",
        f"<b>Usuario:</b> {header.id_usuario}",
        f"<b>Estado:</b> {header.estado_movimiento_inventario}",
    ]
    for line in info_data:
        elements.append(Paragraph(line, info_style))

    if header.comentario:
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"<b>Motivo / Comentario:</b> {header.comentario}", info_style))

    elements.append(Spacer(1, 16))

    # ---- Tabla de productos devueltos ----
    data = [["Código", "Producto", "Lote", "Cantidad"]]
    for m in movimientos:
        data.append([
            m.id_lote.id_producto.codigo_producto,
            m.id_lote.id_producto.nombre,
            m.id_lote.numero_lote,
            str(m.cantidad),
        ])

    table = Table(data, hAlign="LEFT", repeatRows=1, colWidths=[90, 350, 100, 80])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F5EC")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0B3F2E")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.gray),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
    ]))

    elements.append(table)
    doc.build(elements)

    return response


@login_required
def buscar_facturas_completadas(request):
    """
    Devuelve una lista de facturas (referencia_transaccion y fecha)
    que tengan movimientos de tipo 'VEN' con estado 'Completado'.
    Se usa para el modal de búsqueda de facturas.
    """
    term = (request.GET.get("term") or "").strip().lower()

    facturas = (
        Movimientos_Inventario_Sucursal.objects
        .filter(
            id_tipo_movimiento__codigo="VEN",
            estado_movimiento_inventario__nombre_estado="Completado"
        )
        .values("referencia_transaccion")
        .annotate(
            total=Sum("cantidad"),
            fecha=Max("fecha_hora")  # ✅ tomamos la última fecha de movimiento
        )
        .order_by("-fecha")
    )

    if term:
        facturas = facturas.filter(referencia_transaccion__icontains=term)

    data = [
        {
            "referencia": f["referencia_transaccion"],
            "fecha": f["fecha"].strftime("%Y-%m-%d %H:%M") if f["fecha"] else "",
            "total": abs(f["total"] or 0)
        }
        for f in facturas if f["referencia_transaccion"]
    ]
    return JsonResponse(data, safe=False)


from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def productos_por_factura(request, ref):
    """
    Devuelve los productos asociados a una factura (referencia_transaccion)
    que correspondan a movimientos de tipo 'VEN' completados.
    """
    term = (request.GET.get("term") or "").strip().lower()

    movimientos = (
        Movimientos_Inventario_Sucursal.objects
        .filter(
            id_tipo_movimiento__codigo="VEN",
            estado_movimiento_inventario__nombre_estado="Completado",
            referencia_transaccion=ref
        )
        .select_related("id_lote__id_producto")
        .order_by("id_lote__id_producto__nombre")
    )

    # ✅ Filtro de búsqueda correcto
    if term:
        movimientos = movimientos.filter(id_lote__id_producto__nombre__icontains=term)

    productos = {}
    for mov in movimientos:
        prod = mov.id_lote.id_producto
        productos[prod.id] = {
            "id": prod.id,
            "codigo": prod.codigo_producto,
            "nombre": prod.nombre,
            "descripcion": prod.descripcion or "",
            "presentacion": getattr(prod.id_presentacion, "nombre_presentacion", ""),
            "unidad": getattr(prod.id_unidad_medida, "nombre_unidad_medida", ""),
            "condicion": getattr(prod.id_condicion_almacenamiento, "nombre_condicion", ""),
            "receta": prod.requiere_receta,
            "controlado": prod.es_controlado,
        }

    return JsonResponse(list(productos.values()), safe=False)
