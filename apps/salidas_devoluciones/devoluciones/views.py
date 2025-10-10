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


# ============================================================
# LISTA
# ============================================================

@login_required
def devolucion_list(request):
    """
    Tabla de devoluciones. Mostramos una fila por movimiento más reciente
    de cada referencia (No. de factura) con tipo DEV.
    """
    movs = (
        Movimientos_Inventario_Sucursal.objects
        .filter(id_tipo_movimiento__codigo="DEV")
        .select_related("id_usuario", "estado_movimiento_inventario")
        .order_by("-id")[:200]
    )

    devoluciones = []
    for m in movs:
        devoluciones.append({
            "referencia_transaccion": m.referencia_transaccion,
            "fecha": m.fecha_hora,
            "usuario": m.id_usuario,
            "estado": m.estado_movimiento_inventario,
        })

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
