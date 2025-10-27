# apps/alertas_vencimientos/vencimientos/views.py
from __future__ import annotations

import json
import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Exists, OuterRef
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string

from .forms import ReporteVencimientoForm
from apps.alertas_vencimientos.models import Reportes_Vencimiento, Detalle_Reporte_Vencimiento
from apps.inventario.models import Lotes, Productos
from apps.mantenimiento.models import Estado_Vencimiento, Estado_Lote

logger = logging.getLogger(__name__)

PROXIMO_DIAS = getattr(settings, "PROXIMO_VENCER_DIAS", 30)

# Transiciones permitidas en el reporte
TRANSICIONES = {
    "Completado": {"Enviado", "Cancelado"},
    "Enviado": set(),
    "Cancelado": set(),
}

def _estado_lote_por_regla(lote, hoy, proximo_dias):
    if lote.fecha_caducidad and lote.fecha_caducidad < hoy:
        nombre = "Vencido"
    elif lote.fecha_caducidad and (lote.fecha_caducidad - hoy).days <= proximo_dias:
        nombre = "Próximo a Vencer"
    else:
        nombre = "Disponible"
    return Estado_Lote.objects.only("id").get(nombre_estado=nombre).id

@login_required
def reporte_cambiar_estado_modal(request, reporte_id):
    reporte = get_object_or_404(Reportes_Vencimiento, pk=reporte_id)
    estados = Estado_Vencimiento.objects.filter(
        nombre_estado__in=["Completado", "Enviado", "Cancelado"]
    ).order_by("nombre_estado")

    actual = reporte.id_estado.nombre_estado
    permitidos = TRANSICIONES.get(actual, set())

    html = render_to_string(
        "vencimientos/partials/cambiar_estado.html",
        {"reporte": reporte, "estados": estados, "actual": actual, "permitidos": permitidos},
        request=request,
    )
    return JsonResponse({"html": html})

@login_required
@require_POST
@transaction.atomic
def reporte_cambiar_estado(request, reporte_id):
    reporte = get_object_or_404(Reportes_Vencimiento, pk=reporte_id)
    nuevo_id = request.POST.get("estado_id")

    try:
        nuevo_estado = Estado_Vencimiento.objects.get(pk=nuevo_id)
    except Estado_Vencimiento.DoesNotExist:
        return JsonResponse({"success": False, "error": "Estado inválido."}, status=400)

    actual = reporte.id_estado.nombre_estado
    if nuevo_estado.nombre_estado not in TRANSICIONES.get(actual, set()):
        return JsonResponse({
            "success": False,
            "error": f"No se puede pasar de {actual} a {nuevo_estado.nombre_estado}."
        }, status=400)

    if nuevo_estado.nombre_estado == "Cancelado":
        hoy = timezone.now().date()
        id_devuelto = Estado_Lote.objects.only("id").get(nombre_estado="Devuelto").id

        detalles = (
            Detalle_Reporte_Vencimiento.objects
            .select_related("id_lote")
            .select_for_update()
            .filter(id_reporte=reporte)
        )

        for d in detalles:
            lote = d.id_lote
            if lote.id_estado_lote_id != id_devuelto or (lote.cantidad_disponible or 0) != 0:
                return JsonResponse({
                    "success": False,
                    "error": f"El lote {lote.numero_lote} fue modificado después del reporte; "
                             "no se puede cancelar automáticamente."
                }, status=409)

        for d in detalles:
            lote = d.id_lote
            lote.cantidad_disponible = d.cantidad_reportada
            lote.id_estado_lote_id = _estado_lote_por_regla(lote, hoy, PROXIMO_DIAS)
            lote.save(update_fields=["cantidad_disponible", "id_estado_lote"])

    reporte.id_estado = nuevo_estado
    reporte.save(update_fields=["id_estado"])
    return JsonResponse({"success": True})


# -----------------------------------------------------------
# LISTA DE REPORTES DE VENCIMIENTO
# -----------------------------------------------------------
@login_required
def reporte_vencimiento_list(request):
    reportes = (
        Reportes_Vencimiento.objects
        .select_related("id_usuario", "id_estado")
        .order_by("-fecha_reporte")
    )
    return render(request, "vencimientos/lista.html", {"reportes": reportes})



# -----------------------------------------------------------
# CREAR REPORTE DE VENCIMIENTO (solo lotes vencidos)
# -----------------------------------------------------------
@login_required
@transaction.atomic
def reporte_vencimiento_create(request):
    """
    Crea un reporte de vencimiento que retira completamente del inventario
    todos los lotes seleccionados que ya están vencidos.
    Al hacerlo, el stock pasa a 0 y el estado del lote cambia a "Retirado".
    """
    if request.method == "GET":
        form = ReporteVencimientoForm()
        today = timezone.now().date()
        return render(request, "vencimientos/partials/form.html", {"form": form, "today": today})

    try:
        data = json.loads((request.body or b"").decode("utf-8"))
        form_data = data.get("form_data", {})
        detalles_data = data.get("detalles", [])

        if not detalles_data:
            raise ValueError("No se enviaron detalles.")

        usuario = request.user
        fecha_reporte = timezone.now().date()
        observaciones = form_data.get("observaciones", "")
        documento = form_data.get("documento", f"Reporte Vencimiento - {fecha_reporte}")

        # Estado del reporte: “Vencido”
        estado_inicial = Estado_Vencimiento.objects.get(nombre_estado="Completado")

        # Crear cabecera del reporte
        reporte = Reportes_Vencimiento.objects.create(
            fecha_reporte=fecha_reporte,
            observaciones=observaciones,
            documento=documento,
            id_usuario=usuario,
            id_estado=estado_inicial,
        )

        hoy = timezone.now().date()

        # Obtener el estado "Retirado" desde la tabla de Estado_Lote
        from apps.mantenimiento.models import Estado_Lote  # Importar dentro para evitar dependencia circular
        try:
            estado_devuelto = Estado_Lote.objects.get(nombre_estado="Devuelto")
        except Estado_Lote.DoesNotExist:
            raise ValueError("No existe el estado 'Devuelto' en la tabla de Estado_Lote.")

        # Procesar cada detalle
        for idx, det in enumerate(detalles_data, start=1):
            lote_id = det.get("lote_id")
            if not lote_id:
                raise ValueError(f"Falta lote en línea {idx}.")

            lote = (
                Lotes.objects
                .select_for_update()
                .select_related("id_producto")
                .get(pk=lote_id)
            )

            # Validar vencimiento
            if not lote.fecha_caducidad or lote.fecha_caducidad >= hoy:
                raise ValueError(f"El lote {lote.numero_lote} aún no ha vencido.")

            # Validar stock
            if lote.cantidad_disponible <= 0:
                raise ValueError(f"El lote {lote.numero_lote} no tiene stock disponible.")

            cantidad_retirada = lote.cantidad_disponible

            # Actualizar el lote (stock y estado)
            lote.cantidad_disponible = 0
            lote.id_estado_lote = estado_devuelto
            lote.save(update_fields=["cantidad_disponible", "id_estado_lote"])

            # Crear detalle del vencimiento
            Detalle_Reporte_Vencimiento.objects.create(
                id_reporte=reporte,
                id_lote=lote,
                cantidad_reportada=cantidad_retirada
            )

        return JsonResponse({"success": True, "reporte_id": reporte.id})

    except ValueError as e:
        # Se lanza error controlado → rollback automático
        transaction.set_rollback(True)
        return JsonResponse({"success": False, "errors": str(e)}, status=400)

    except Exception as e:
        # Errores no controlados → rollback también
        transaction.set_rollback(True)
        logger.exception("Error inesperado al crear reporte de vencimiento")
        return JsonResponse({"success": False, "errors": str(e)}, status=500)


# -----------------------------------------------------------
# CONSULTAR REPORTE DE VENCIMIENTO
# -----------------------------------------------------------
@login_required
def reporte_vencimiento_detail(request, reporte_id):
    reporte = get_object_or_404(Reportes_Vencimiento, pk=reporte_id)
    detalles = (
        Detalle_Reporte_Vencimiento.objects
        .select_related("id_lote__id_producto")
        .filter(id_reporte=reporte)
    )
    return render(request, "vencimientos/partials/consultar.html", {
        "reporte": reporte,
        "detalles": detalles
    })


# -----------------------------------------------------------
# BUSCAR PRODUCTOS (solo con lotes vencidos y stock > 0)
# -----------------------------------------------------------
@login_required
def search_productos(request):
    term = request.GET.get("term", "").strip()
    hoy = timezone.now().date()

    vencidos_qs = Lotes.objects.filter(
        id_producto=OuterRef("pk"),
        fecha_caducidad__lt=hoy,
        cantidad_disponible__gt=0
    )

    productos = (
        Productos.objects
        .annotate(tiene_vencidos=Exists(vencidos_qs))
        .filter(
            Q(nombre__icontains=term) | Q(codigo_producto__icontains=term),
            tiene_vencidos=True, # <-- Ahora es el segundo argumento (keyword)
        )
        .select_related(
            "id_presentacion",
            "id_unidad_medida",
            "id_condicion_almacenamiento"
        )
        .order_by("nombre")[:20]
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


# -----------------------------------------------------------
# BUSCAR LOTES (solo vencidos con stock > 0)
# -----------------------------------------------------------
@login_required
def search_lotes(request, producto_id: int):
    hoy = timezone.now().date()
    term = request.GET.get("term", "").strip()

    qs = (
        Lotes.objects
        .filter(
            id_producto_id=producto_id,
            fecha_caducidad__lt=hoy,
            cantidad_disponible__gt=0
        )
        .filter(Q(numero_lote__icontains=term))
        .order_by("fecha_caducidad")
    )

    results = [
        {
            "id": l.id,
            "numero_lote": l.numero_lote,
            "fecha_caducidad": l.fecha_caducidad.strftime("%Y-%m-%d") if l.fecha_caducidad else "",
            "cantidad": l.cantidad_disponible,
            "dias_vencido": (hoy - l.fecha_caducidad).days,
        }
        for l in qs
    ]
    return JsonResponse(results, safe=False)
