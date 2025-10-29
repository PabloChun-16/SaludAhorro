# apps/recepcion_almacenamiento/views.py
from __future__ import annotations

import json
import logging
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Q
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .forms import RecepcionForm
from .models import Detalle_Recepcion, Recepciones_Envio
from apps.inventario.models import Lotes, Productos
from apps.salidas_devoluciones.models import Movimientos_Inventario_Sucursal
from apps.mantenimiento.models import (
    Estado_Recepcion,
    Estado_Lote,
    Estado_Movimiento_Inventario,
    Tipo_Movimiento_Inventario,
)

from django.http import HttpResponse
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

logger = logging.getLogger(__name__)

from django.views.decorators.http import require_POST

# ------------- utilidades internas -------------
def _get_estado_recepcion(nombre: str) -> Estado_Recepcion:
    return Estado_Recepcion.objects.get(nombre_estado=nombre)

def _get_estado_mov(nombre: str) -> Estado_Movimiento_Inventario:
    return Estado_Movimiento_Inventario.objects.get(nombre_estado=nombre)

# -------------------------------
# Cambio de estado 
# -------------------------------
@login_required
@require_POST
@transaction.atomic
def recepcion_cambiar_estado(request, pk: int):
    """
    Cambia el estado de una recepción:
      - 'Recibido Completo'  <->  'Recibido Parcialmente' : libre
      - 'Rechazado' : valida que no existan movimientos de naturaleza -1
                      (p.ej. VEN, TRB, AJ-) posteriores a la fecha de recepción
                      para los lotes involucrados y no cancelados.
                      Si es válido:
                        * marca TODOS los movimientos REC de esa recepción como 'Cancelado'
                        * resta del stock lo recibido en Detalle_Recepcion
    Body JSON:
      {"nuevo_estado": "Recibido Completo" | "Recibido Parcialmente" | "Rechazado", "motivo": "opcional/obligatorio si rechaza"}
    """
    recepcion = get_object_or_404(
        Recepciones_Envio.objects.select_related("estado_recepcion", "id_usuario"),
        pk=pk
    )

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)

    nuevo_estado_nombre = (data.get("nuevo_estado") or "").strip()
    motivo = (data.get("motivo") or "").strip()

    if nuevo_estado_nombre not in ("Recibido Completo", "Recibido Parcialmente", "Rechazado"):
        return JsonResponse({"success": False, "error": "Estado no permitido."}, status=400)

    # Atajos a estados
    try:
        estado_nuevo = _get_estado_recepcion(nuevo_estado_nombre)
        estado_mov_cancelado = _get_estado_mov("Cancelado")
    except (Estado_Recepcion.DoesNotExist, Estado_Movimiento_Inventario.DoesNotExist):
        return JsonResponse({"success": False, "error": "Catálogo de estados incompleto."}, status=400)

    # Si solo alterna completo/parcial: actualizar y salir
    if nuevo_estado_nombre in ("Recibido Completo", "Recibido Parcialmente"):
        recepcion.estado_recepcion = estado_nuevo
        recepcion.save(update_fields=["estado_recepcion"])
        return JsonResponse({"success": True, "nuevo_estado": nuevo_estado_nombre})

    # Rechazado: validaciones + reversión "blanda"
    if nuevo_estado_nombre == "Rechazado":
        if not motivo:
            return JsonResponse({"success": False, "error": "Debe indicar un motivo para rechazar."}, status=400)

        # Lotes involucrados en esta recepción
        detalles = list(
            Detalle_Recepcion.objects.filter(id_recepcion=recepcion).select_related("id_lote", "id_lote__id_producto")
        )
        if not detalles:
            return JsonResponse({"success": False, "error": "La recepción no tiene detalles."}, status=400)

        lote_ids = [d.id_lote_id for d in detalles]

        # Tipos de naturaleza NEGATIVA (-1)
        tipos_negativos = list(
            Tipo_Movimiento_Inventario.objects.filter(naturaleza=-1).values_list("id", flat=True)
        )

        # ¿Hay movimientos de salida (no cancelados) después de la fecha de recepción?
        conflicto = (
            Movimientos_Inventario_Sucursal.objects
            .filter(
                id_lote_id__in=lote_ids,
                id_tipo_movimiento_id__in=tipos_negativos,
                fecha_hora__gte=recepcion.fecha_recepcion,
            )
            .exclude(estado_movimiento_inventario__nombre_estado="Cancelado")
            .select_related("id_lote", "id_lote__id_producto", "id_tipo_movimiento")
            .order_by("fecha_hora")
            .first()
        )
        if conflicto:
            prod = conflicto.id_lote.id_producto.nombre if hasattr(conflicto.id_lote, "id_producto") else ""
            return JsonResponse({
                "success": False,
                "error": (
                    "No es posible RECHAZAR esta recepción porque existen movimientos posteriores "
                    f"de salida. Ejemplo: {conflicto.id_tipo_movimiento.codigo} "
                    f"({prod}, lote {conflicto.id_lote.numero_lote}) en {timezone.localtime(conflicto.fecha_hora).strftime('%d/%m/%Y %H:%M')}."
                )
            }, status=400)

        # 1) Marcar todos los REC de esta recepción como Cancelado
        Movimientos_Inventario_Sucursal.objects.filter(
            referencia_transaccion=recepcion.numero_envio_bodega,
            id_tipo_movimiento__codigo="REC",
        ).update(estado_movimiento_inventario=estado_mov_cancelado, comentario=motivo)

        # 2) Revertir stock (restar lo que sumó la recepción)
        for d in detalles:
            Lotes.objects.filter(pk=d.id_lote_id).update(
                cantidad_disponible=F("cantidad_disponible") - int(d.cantidad_recibida or 0)
            )

        # 3) Guardar estado en el header
        recepcion.estado_recepcion = estado_nuevo
        recepcion.save(update_fields=["estado_recepcion"])

        return JsonResponse({"success": True, "nuevo_estado": nuevo_estado_nombre})
    
# -------------------------------
# Listado y detalle de recepciones
# -------------------------------
@login_required
def recepcion_list(request):
    recepciones = Recepciones_Envio.objects.select_related("id_usuario", "estado_recepcion")
    return render(request, "recepcion/lista.html", {"recepciones": recepciones})


@login_required
def recepcion_detail(request, pk):
    recepcion = get_object_or_404(
        Recepciones_Envio.objects.select_related("id_usuario", "estado_recepcion"),
        pk=pk,
    )
    detalles = (
        Detalle_Recepcion.objects
        .filter(id_recepcion=recepcion)
        .select_related("id_lote", "id_lote__id_producto")
    )

    # Comentario (si lo guardaste en movimientos con la misma referencia)
    comentario = (
        Movimientos_Inventario_Sucursal.objects
        .filter(referencia_transaccion=recepcion.numero_envio_bodega)
        .exclude(comentario__isnull=True).exclude(comentario="")
        .values_list("comentario", flat=True)
        .first()
    )

    total = sum((d.costo_unitario or 0) * (d.cantidad_recibida or 0) for d in detalles)

    return render(
        request,
        "recepcion/partials/_consultar.html",
        {"recepcion": recepcion, "detalles": detalles, "comentario": comentario, "total": total},
    )


@login_required
def recepcion_graficas(request):
    """Vista simple de gráficas para Recepciones."""
    qs = Recepciones_Envio.objects.all().values("estado_recepcion", "fecha_recepcion")

    estados = {}
    for r in qs:
        key = r.get("estado_recepcion") or "Otros"
        estados[key] = estados.get(key, 0) + 1

    from datetime import timedelta
    today = timezone.localdate()
    labels = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    diarios = {d: 0 for d in labels}
    for r in qs:
        dt = r.get("fecha_recepcion")
        if dt:
            d = dt.date()
            if d in diarios:
                diarios[d] += 1

    context = {
        "labels_dias": [d.strftime("%d/%m") for d in labels],
        "data_dias": [diarios[d] for d in labels],
        "labels_estados": list(estados.keys()),
        "data_estados": list(estados.values()),
    }
    return render(request, "recepcion/graficas.html", context)


# -------------------------------
# Búsquedas vía AJAX
# -------------------------------
@login_required
def search_productos(request):
    term = request.GET.get("term", "").strip()

    productos = (
        Productos.objects
        .select_related("id_presentacion", "id_unidad_medida", "id_condicion_almacenamiento", "id_estado_producto")
        .filter(
            Q(nombre__icontains=term) | Q(codigo_producto__icontains=term),
            id_estado_producto__nombre_estado__iexact="Activo",   # <- SOLO activos
        )
        [:20]
    )

    results = []
    for p in productos:
        results.append({
            "id": p.id,
            "codigo": p.codigo_producto,
            "nombre": p.nombre,
            "descripcion": p.descripcion or "",
            # 👇 usa __str__ de cada FK; si es NULL, devuelve ""
            "presentacion": str(p.id_presentacion) if p.id_presentacion_id else "",
            "unidad": str(p.id_unidad_medida) if p.id_unidad_medida_id else "",
            "condicion": str(p.id_condicion_almacenamiento) if p.id_condicion_almacenamiento_id else "",
            "receta": bool(p.requiere_receta),
            "controlado": bool(p.es_controlado),
        })
    return JsonResponse(results, safe=False)

@login_required
def search_lotes(request, producto_id: int):
    """
    Lista lotes de un producto (filtro por número parcial).
    """
    term = request.GET.get("term", "").strip()
    qs = (
        Lotes.objects
        .select_related("id_estado_lote")
        .filter(
            id_producto_id=producto_id,
            id_estado_lote__nombre_estado__in=["Disponible", "Próximo a Vencer"],  # <- SOLO estos estados
        )
    )
    
    if term:
        qs = qs.filter(numero_lote__icontains=term)

    lotes = qs.order_by("-id")[:20]
    results = [
        {
            "id": l.id,
            "numero_lote": l.numero_lote,
            "fecha_caducidad": l.fecha_caducidad.strftime("%Y-%m-%d") if l.fecha_caducidad else "",
            "cantidad": l.cantidad_disponible,
        }
        for l in lotes
    ]
    return JsonResponse(results, safe=False)


# -------------------------------
# Crear lote vía AJAX
# -------------------------------
@login_required
def create_lote(request):
    """
    Crea un lote nuevo para un producto.
    Valida número de lote y fecha. Evita IDs "mágicos" usando Estado_Lote por nombre.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido.")

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)

    producto_id = data.get("producto_id")
    numero = (data.get("numero_lote") or "").strip()
    caducidad = (data.get("fecha_caducidad") or "").strip()
    ubicacion = (data.get("ubicacion") or "").strip()

    if not producto_id or not numero:
        return JsonResponse({"success": False, "error": "Datos incompletos."}, status=400)

    fecha_caducidad = None
    if caducidad:
        try:
            fecha_caducidad = datetime.strptime(caducidad, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"success": False, "error": "Formato de fecha inválido."}, status=400)

    try:
        estado_disponible = Estado_Lote.objects.get(nombre_estado="Disponible")
    except Estado_Lote.DoesNotExist:
        return JsonResponse({"success": False, "error": "No existe el estado 'Disponible'."}, status=400)

    lote = Lotes.objects.create(
        id_producto_id=producto_id,
        numero_lote=numero,
        fecha_caducidad=fecha_caducidad,
        cantidad_disponible=0,
        ubicacion_almacen=ubicacion or None,
        precio_compra=None,
        precio_venta=None,
        id_estado_lote=estado_disponible,
    )

    return JsonResponse(
        {
            "success": True,
            "id": lote.id,
            "numero_lote": lote.numero_lote,
            "fecha_caducidad": lote.fecha_caducidad.strftime("%Y-%m-%d") if lote.fecha_caducidad else "",
        }
    )


# -------------------------------
# Crear recepción (form + detalle)
# -------------------------------
@login_required
@transaction.atomic
def recepcion_create(request):
    """
    Guarda una recepción completa.
    Acepta payload JSON (fetch) con:
    {
      "form_data": {"numero_envio_bodega": "...", "fecha_recepcion": "YYYY-MM-DDTHH:MM"},
      "detalles": [
         {
           "producto_id": 123,
           "lote_id": 456,                 # opcional si se selecciona un lote ya existente
           "numero_lote": "A-001",         # requerido si NO se manda lote_id
           "fecha_caducidad": "2025-11-30",# requerido si NO se manda lote_id
           "cantidad_recibida": 10,
           "costo_unitario": 2.5
         }, ...
      ],
      "comentario": "texto opcional"
    }
    Si el front enviara form-url-encoded, cae a un fallback con items_json.
    """
    if request.method == "GET":
        form = RecepcionForm()
        return render(request, "recepcion/partials/form.html", {"form": form})

    # POST
    try:
        # 1) Intenta JSON (fetch)
        try:
            data = json.loads((request.body or b"").decode("utf-8"))
            form_data = data.get("form_data", {})
            detalles_data = data.get("detalles", [])
            comentario = (data.get("comentario") or "").strip()
        except json.JSONDecodeError:
            # 2) Fallback a form-url-encoded + items_json
            form_data = request.POST.dict()
            detalles_data = json.loads(request.POST.get("items_json", "[]"))
            comentario = (form_data.get("comentario") or "").strip()

        form = RecepcionForm(form_data)
        if not form.is_valid():
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        if not detalles_data:
            return JsonResponse({"success": False, "errors": "No se enviaron detalles de productos."}, status=400)

        # Estados y tipo de movimiento requeridos
        try:
            estado_recepcion = Estado_Recepcion.objects.get(nombre_estado="Recibido Completo")
        except Estado_Recepcion.DoesNotExist:
            return JsonResponse(
                {"success": False, "errors": "No existe el estado 'Recibido Completo'."},
                status=400,
            )
        try:
            tipo_mov_recepcion = Tipo_Movimiento_Inventario.objects.get(codigo="REC")
        except Tipo_Movimiento_Inventario.DoesNotExist:
            return JsonResponse({"success": False, "errors": "No existe el tipo REC."}, status=400)
        try:
            estado_mov = Estado_Movimiento_Inventario.objects.get(nombre_estado="Completado")
        except Estado_Movimiento_Inventario.DoesNotExist:
            return JsonResponse(
                {"success": False, "errors": "No existe el estado de movimiento 'Completado'."}, status=400
            )

        # request.user debe ser tu modelo Usuario si AUTH_USER_MODEL está bien configurado
        usuario_instance = request.user

        # Encabezado
        recepcion = form.save(commit=False)
        recepcion.id_usuario = usuario_instance
        recepcion.estado_recepcion = estado_recepcion
        recepcion.save()

        # Detalles
        for idx, det in enumerate(detalles_data, start=1):
            producto_id = det.get("producto_id")
            lote_id = det.get("lote_id")
            numero_lote = (det.get("numero_lote") or "").strip()
            fecha_caducidad_str = det.get("fecha_caducidad")
            cantidad_raw = det.get("cantidad_recibida")
            costo_raw = det.get("costo_unitario")

            # Validaciones de presencia
            if not producto_id:
                raise ValidationError(f"Falta producto en línea {idx}.")
            if not lote_id and not numero_lote:
                raise ValidationError(f"Falta número de lote en línea {idx}.")
            if not fecha_caducidad_str and not lote_id:
                raise ValidationError(f"Falta fecha de caducidad en línea {idx}.")

            # Conversión y validación de cantidad y costo
            try:
                cantidad = int(cantidad_raw or 0)
                if cantidad <= 0:
                    raise ValidationError(f"Cantidad inválida en línea {idx}.")
            except (TypeError, ValueError):
                raise ValidationError(f"Cantidad inválida en línea {idx}.")

            try:
                costo = float(costo_raw or 0.0)
            except (TypeError, ValueError):
                raise ValidationError(f"Costo inválido en línea {idx}.")

            # Parse de fecha (si viene)
            fecha_caducidad = None
            if fecha_caducidad_str:
                try:
                    fecha_caducidad = datetime.strptime(fecha_caducidad_str, "%Y-%m-%d").date()
                except ValueError:
                    raise ValidationError(f"Fecha de caducidad inválida en línea {idx}.")

            # Entidades
            producto = get_object_or_404(Productos, pk=producto_id)

            # Resolver lote
            if lote_id:
                lote = get_object_or_404(Lotes, pk=lote_id)
            else:
                # Crea o toma el lote del producto por número
                lote, _creado = Lotes.objects.get_or_create(
                    id_producto=producto,
                    numero_lote=numero_lote,
                    defaults={"fecha_caducidad": fecha_caducidad, "cantidad_disponible": 0},
                )

            # Sumar stock de forma segura (evita race conditions)
            Lotes.objects.filter(pk=lote.pk).update(cantidad_disponible=F("cantidad_disponible") + cantidad)
            lote.refresh_from_db(fields=["cantidad_disponible"])

            # Detalle de recepción
            Detalle_Recepcion.objects.create(
                id_recepcion=recepcion,
                id_lote=lote,
                cantidad_recibida=cantidad,
                costo_unitario=costo,
            )

            # Auditoría de inventario
            Movimientos_Inventario_Sucursal.objects.create(
                id_lote=lote,
                id_tipo_movimiento=tipo_mov_recepcion,
                cantidad=cantidad,
                id_usuario=usuario_instance,
                referencia_transaccion=recepcion.numero_envio_bodega,
                comentario=comentario or None,
                estado_movimiento_inventario=estado_mov,
            )

        return JsonResponse({"success": True, "recepcion_id": recepcion.id})

    except ValidationError as e:
        return JsonResponse({"success": False, "errors": str(e)}, status=400)
    except Exception as e:
        logger.exception("Ocurrió un error inesperado al procesar la recepción.")
        return JsonResponse({"success": False, "errors": str(e)}, status=500)


@login_required
def recepcion_export_pdf(request, pk):
    recepcion = get_object_or_404(
        Recepciones_Envio.objects.select_related("id_usuario", "estado_recepcion"),
        pk=pk
    )
    detalles = (
        Detalle_Recepcion.objects
        .filter(id_recepcion=recepcion)
        .select_related("id_lote", "id_lote__id_producto")
    )

    comentario = (
        Movimientos_Inventario_Sucursal.objects
        .filter(referencia_transaccion=recepcion.numero_envio_bodega)
        .exclude(comentario__isnull=True).exclude(comentario="")
        .values_list("comentario", flat=True)
        .first()
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Recepcion_{recepcion.numero_envio_bodega}.pdf"'

    buffer = []
    doc = SimpleDocTemplate(response, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Titulo", fontSize=16, leading=20, spaceAfter=10, textColor=colors.HexColor("#0f7a3a"), alignment=1))
    styles.add(ParagraphStyle(name="Seccion", fontSize=12, leading=14, spaceAfter=6, textColor=colors.HexColor("#074d24"), fontName='Helvetica-Bold'))

    contenido = []

    # Título
    contenido.append(Paragraph("Reporte de Recepción", styles["Titulo"]))
    contenido.append(Spacer(1, 8))

    # Datos generales
    contenido.append(Paragraph(f"<b>N.º de Envío:</b> {recepcion.numero_envio_bodega}", styles["Normal"]))
    contenido.append(Paragraph(f"<b>Usuario:</b> {recepcion.id_usuario}", styles["Normal"]))
    contenido.append(Paragraph(f"<b>Fecha:</b> {recepcion.fecha_recepcion.strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    contenido.append(Paragraph(f"<b>Estado:</b> {recepcion.estado_recepcion}", styles["Normal"]))
    contenido.append(Spacer(1, 10))

    # Tabla de productos
    contenido.append(Paragraph("Productos Recibidos", styles["Seccion"]))
    data = [["Código", "Producto", "Lote", "Caducidad", "Cantidad", "Costo Unit."]]
    total = 0

    for d in detalles:
        codigo = d.id_lote.id_producto.codigo_producto
        nombre = d.id_lote.id_producto.nombre
        lote = d.id_lote.numero_lote
        cad = d.id_lote.fecha_caducidad.strftime("%d/%m/%Y") if d.id_lote.fecha_caducidad else ""
        cant = d.cantidad_recibida
        costo = d.costo_unitario
        total += (costo or 0) * (cant or 0)
        data.append([codigo, nombre, lote, cad, cant, f"Q{costo:.2f}"])

    table = Table(data, colWidths=[90, 280, 80, 80, 60, 60])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e8f5ec")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#0b3f2e")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    contenido.append(table)
    contenido.append(Spacer(1, 10))

    # Total
    contenido.append(Paragraph(f"<b>Total estimado:</b> Q{total:.2f}", styles["Normal"]))

    # Comentario
    if comentario:
        contenido.append(Spacer(1, 10))
        contenido.append(Paragraph("Comentario:", styles["Seccion"]))
        contenido.append(Paragraph(comentario, styles["Normal"]))

    doc.build(contenido)
    return response