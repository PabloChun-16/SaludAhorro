from __future__ import annotations
import json
import logging
from datetime import date
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Q, Exists, OuterRef
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .forms import ReporteVencimientoForm
from apps.alertas_vencimientos.models import Reportes_Vencimiento, Detalle_Reporte_Vencimiento
from apps.inventario.models import Lotes, Productos
from apps.mantenimiento.models import Estado_Vencimiento

logger = logging.getLogger(__name__)


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
        estado_venc = Estado_Vencimiento.objects.get(nombre_estado="Vencido")

        # Crear cabecera del reporte
        reporte = Reportes_Vencimiento.objects.create(
            fecha_reporte=fecha_reporte,
            observaciones=observaciones,
            documento=documento,
            id_usuario=usuario,
            id_estado=estado_venc,
        )

        hoy = timezone.now().date()

        # Obtener el estado "Retirado" desde la tabla de Estado_Lote
        from apps.mantenimiento.models import Estado_Lote  # Importar dentro para evitar dependencia circular
        try:
            estado_retirado = Estado_Lote.objects.get(nombre_estado="Retirado")
        except Estado_Lote.DoesNotExist:
            raise ValueError("No existe el estado 'Retirado' en la tabla de Estado_Lote.")

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
            lote.id_estado_lote = estado_retirado
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
