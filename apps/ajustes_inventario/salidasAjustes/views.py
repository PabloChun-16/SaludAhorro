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
        .select_related("id_presentacion", "id_unidad_medida", "id_condicion_almacenamiento")
        .filter(Q(nombre__icontains=term) | Q(codigo_producto__icontains=term))[:20]
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
    qs = Lotes.objects.filter(id_producto_id=producto_id)
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
