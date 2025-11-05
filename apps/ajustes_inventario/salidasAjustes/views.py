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

from .forms import AjusteSalidaForm
from apps.ajustes_inventario.models import Inventario_Fisico, Detalle_Conteo
from apps.inventario.models import Lotes, Productos
from apps.mantenimiento.models import Estado_Lote

from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


logger = logging.getLogger(__name__)


# -----------------------------------------
# LISTADO DE AJUSTES (SALIDAS)
# -----------------------------------------
@login_required
def ajuste_salida_list(request):
    ajustes = Inventario_Fisico.objects.select_related("id_usuario")\
    .filter(tipo_ajuste="Salida").order_by("-fecha_conteo")
    return render(request, "salidasAjustes/lista.html", {"ajustes": ajustes})


# -----------------------------------------
# CREAR AJUSTE DE INVENTARIO (SALIDA)
# -----------------------------------------
@login_required
@transaction.atomic
def ajuste_salida_create(request):
    """
    Guarda un registro de ajuste por salida (usa Inventario_Fisico y Detalle_Conteo).
    """
    if request.method == "GET":
        form = AjusteSalidaForm()
        today = timezone.now().date()
        return render(request, "salidasAjustes/partials/form.html", {"form": form, "today": today})

    try:
        data = json.loads((request.body or b"").decode("utf-8"))
        form_data = data.get("form_data", {})
        detalles_data = data.get("detalles", [])

        if not detalles_data:
            return JsonResponse({"success": False, "errors": "No se enviaron detalles del ajuste."}, status=400)

        # === Usuario y fecha ===
        usuario = request.user
        fecha_ajuste = form_data.get("fecha_ajuste") or timezone.now().date()

        # === Crear encabezado ===
        ajuste = Inventario_Fisico.objects.create(
            id_usuario=usuario,
            fecha_conteo=fecha_ajuste,
            estado="Completado",
            tipo_ajuste="Salida"
        )

        # === Crear detalles ===
        for idx, det in enumerate(detalles_data, start=1):
            producto_id = det.get("producto_id")
            lote_id = det.get("lote_id")
            numero_lote = (det.get("numero_lote") or "").strip()
            cantidad_raw = det.get("cantidad_ajustada")

            if not producto_id:
                raise ValidationError(f"Falta producto en línea {idx}.")
            if not lote_id and not numero_lote:
                raise ValidationError(f"Falta número de lote en línea {idx}.")

            try:
                cantidad = int(cantidad_raw or 0)
                if cantidad <= 0:
                    raise ValidationError(f"Cantidad inválida en línea {idx}.")
            except (TypeError, ValueError):
                raise ValidationError(f"Cantidad inválida en línea {idx}.")

            producto = get_object_or_404(Productos, pk=producto_id)

            # Resolver lote
            if lote_id:
                lote = get_object_or_404(Lotes, pk=lote_id)
            else:
                raise ValidationError(f"No se puede crear nuevo lote en una salida (línea {idx}).")

            cantidad_sistema = lote.cantidad_disponible or 0

            # === Actualizar stock (SALIDA: RESTA) ===
            if cantidad > cantidad_sistema:
                raise ValidationError(
                    f"La cantidad a retirar ({cantidad}) supera el stock disponible ({cantidad_sistema}) "
                    f"en el lote {lote.numero_lote}."
                )

            Lotes.objects.filter(pk=lote.pk).update(
                cantidad_disponible=F("cantidad_disponible") - cantidad
            )
            lote.refresh_from_db(fields=["cantidad_disponible"])

            # Crear detalle del conteo
            Detalle_Conteo.objects.create(
                id_conteo=ajuste,
                id_lote=lote,
                cantidad_sistema=cantidad_sistema,
                cantidad_contada=cantidad_sistema - cantidad,
                diferencia=-cantidad,  # 👈 salida = diferencia negativa
            )

        return JsonResponse({"success": True, "ajuste_id": ajuste.id})

    except ValidationError as e:
        return JsonResponse({"success": False, "errors": str(e)}, status=400)
    except Exception as e:
        logger.exception("Error al crear ajuste de inventario (salida)")
        return JsonResponse({"success": False, "errors": str(e)}, status=500)


# -----------------------------------------
# BÚSQUEDAS AJAX
# -----------------------------------------
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
    results = [
        {
            "id": p.id,
            "codigo": p.codigo_producto,
            "nombre": p.nombre,
            "descripcion": p.descripcion or "",
            "presentacion": str(p.id_presentacion) if p.id_presentacion_id else "",
            "unidad": str(p.id_unidad_medida) if p.id_unidad_medida_id else "",
            "condicion": str(p.id_condicion_almacenamiento) if p.id_condicion_almacenamiento_id else "",
            "receta": bool(p.requiere_receta),
            "controlado": bool(p.es_controlado),
        }
        for p in productos
    ]
    return JsonResponse(results, safe=False)


@login_required
def search_lotes(request, producto_id: int):
    term = request.GET.get("term", "").strip()
    allowed_states = ["Disponible", "Próximo a Vencer", "Proximo a Vencer"]
    qs = (
        Lotes.objects
        .filter(
            id_producto_id=producto_id,
            id_estado_lote__nombre_estado__in=allowed_states,
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


@login_required
def create_lote(request):
    """
    Para salidas, normalmente NO se crean nuevos lotes,
    pero se mantiene esta vista para mantener estructura paralela.
    """
    return JsonResponse({"success": False, "error": "No se pueden crear lotes desde salidas."}, status=400)


# -----------------------------------------
# CONSULTAR AJUSTE (SALIDA)
# -----------------------------------------
@login_required
def ajuste_salida_detail(request, ajuste_id):
    ajuste = get_object_or_404(Inventario_Fisico, pk=ajuste_id)
    detalles = Detalle_Conteo.objects.select_related("id_lote__id_producto").filter(id_conteo=ajuste)
    return render(request, "salidasAjustes/partials/consultar.html", {
        "ajuste": ajuste,
        "detalles": detalles
    })


# -----------------------------------------
# ANULAR AJUSTE (SALIDA)
# -----------------------------------------
@login_required
@transaction.atomic
def anular_ajuste_salida(request, ajuste_id: int):
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido.")

    ajuste = get_object_or_404(Inventario_Fisico, pk=ajuste_id)

    if (ajuste.estado or "").lower() in {"cancelado", "anulado"}:
        return JsonResponse({"success": False, "error": "El ajuste ya está cancelado."}, status=400)

    detalles = list(
        Detalle_Conteo.objects.select_related("id_lote").filter(id_conteo=ajuste)
    )
    if not detalles:
        return JsonResponse({"success": False, "error": "El ajuste no tiene detalles."}, status=400)

    lotes_ids = [d.id_lote_id for d in detalles]
    lotes_map = {l.id: l for l in Lotes.objects.select_for_update().filter(id__in=lotes_ids)}

    # 1) Revertir salidas: devolvemos el stock restado.
    for det in detalles:
        lote = lotes_map[det.id_lote_id]
        delta = abs(det.diferencia or 0)  # diferencia era negativa, revertimos positivo
        Lotes.objects.filter(pk=lote.pk).update(
            cantidad_disponible=F("cantidad_disponible") + delta
        )

    # 2) Marcar como cancelado
    ajuste.estado = "Cancelado"
    ajuste.save(update_fields=["estado"])

    return JsonResponse({"success": True})


@login_required
def ajuste_salida_export_pdf(request, ajuste_id):
    """
    Genera un PDF horizontal (landscape) con el detalle del ajuste de inventario (salida).
    Se abre directamente en el navegador.
    """
    ajuste = get_object_or_404(Inventario_Fisico, pk=ajuste_id)
    detalles = (
        Detalle_Conteo.objects
        .select_related("id_lote__id_producto")
        .filter(id_conteo=ajuste)
    )

    # --- Configuración del PDF ---
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=40,
    )
    elements = []
    styles = getSampleStyleSheet()

    # --- Encabezado ---
    title = Paragraph("<b>AJUSTE DE INVENTARIO - SALIDA</b>", styles["Title"])
    subtitle = Paragraph("SAIF · Sistema de Administración e Inventario Farmacéutico", styles["Normal"])
    elements.extend([title, subtitle, Spacer(1, 12)])

    # --- Información general ---
    info_data = [
        ["ID Ajuste:", f"{ajuste.id}"],
        ["Usuario:", f"{ajuste.id_usuario.nombre} {ajuste.id_usuario.apellido}"],
        ["Fecha del Ajuste:", ajuste.fecha_conteo.strftime("%d/%m/%Y")],
        ["Estado:", ajuste.estado],
    ]
    info_table = Table(info_data, colWidths=[150, 500])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.extend([info_table, Spacer(1, 12)])

    # --- Tabla de detalles ---
    data = [["Código", "Producto", "Lote", "Cantidad Anterior", "Cantidad Nueva", "Diferencia (−)"]]
    for d in detalles:
        data.append([
            d.id_lote.id_producto.codigo_producto,
            d.id_lote.id_producto.nombre,
            d.id_lote.numero_lote or "-",
            str(d.cantidad_sistema),
            str(d.cantidad_contada),
            str(d.diferencia),
        ])

    table = Table(data, colWidths=[80, 250, 100, 100, 100, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightcoral),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(table)

    # --- Construcción del PDF ---
    doc.build(elements)
    buffer.seek(0)

    # --- Mostrar PDF en navegador ---
    filename = f"Ajuste_Salida_{ajuste.id}.pdf"
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response
