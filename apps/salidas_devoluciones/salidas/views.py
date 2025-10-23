from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
import json

from apps.mantenimiento.models import (
    Tipo_Movimiento_Inventario,
    Estado_Movimiento_Inventario,
)

from apps.inventario.models import Productos
from apps.inventario.models import Lotes
from apps.salidas_devoluciones.models import Movimientos_Inventario_Sucursal

from django.views.decorators.http import require_POST
from django.db.models import Sum

@login_required
@require_POST
@transaction.atomic
def venta_cancel(request, ref: str):
    # Estados requeridos
    try:
        estado_ok = Estado_Movimiento_Inventario.objects.get(nombre_estado="Completado")
        estado_cancel = Estado_Movimiento_Inventario.objects.get(nombre_estado="Cancelado")
    except Estado_Movimiento_Inventario.DoesNotExist:
        return JsonResponse({"success": False, "errors": ["Faltan estados 'Completado'/'Cancelado' en catálogo."]}, status=400)

    # Movimientos de esta venta
    movs = (
        Movimientos_Inventario_Sucursal.objects
        .filter(id_tipo_movimiento__codigo="VEN", referencia_transaccion=ref)
        .select_for_update()
    )
    if not movs.exists():
        return JsonResponse({"success": False, "errors": [f"No hay movimientos para la referencia '{ref}'."]}, status=404)

    # ¿Ya cancelada?
    if movs.filter(estado_movimiento_inventario=estado_cancel).exists():
        return JsonResponse({"success": False, "errors": [f"La venta '{ref}' ya está cancelada."]}, status=400)

    # Debe haber al menos un movimiento completado para poder cancelar
    if not movs.filter(estado_movimiento_inventario=estado_ok).exists():
        return JsonResponse({"success": False, "errors": [f"La venta '{ref}' no está en estado 'Completado'."]}, status=400)

    usuario = request.user

    try:
        # Recorremos cada movimiento y revertimos exactamente ese lote/cantidad
        for m in movs:
            # m.cantidad es NEGATIVA en ventas; devolvemos su valor absoluto al stock
            devolver = abs(int(m.cantidad or 0))
            if devolver <= 0:
                continue

            # 1) Restaurar stock del lote
            Lotes.objects.filter(pk=m.id_lote_id).update(
                cantidad_disponible=F("cantidad_disponible") + devolver
            )

            # 2) Registrar movimiento de reverso (cantidad POSITIVA),
            #    mismo tipo "VEN", pero estado Cancelado
            Movimientos_Inventario_Sucursal.objects.create(
                id_lote=m.id_lote,
                id_tipo_movimiento=m.id_tipo_movimiento,  # "VEN"
                cantidad=devolver,
                id_usuario=usuario,
                referencia_transaccion=ref,
                comentario=f"Anulación de venta ref {ref} (origen mov {m.id}).",
                estado_movimiento_inventario=estado_cancel,
            )

        # 3) Marcar los movimientos originales como Cancelado (para auditoría visual)
        movs.update(estado_movimiento_inventario=estado_cancel)

        return JsonResponse({"success": True})
    except Exception:
        transaction.set_rollback(True)
        return JsonResponse({"success": False, "errors": ["No se pudo cancelar la venta (error interno)."]}, status=500)
    
@login_required
def venta_list(request):
    """
    Listado de ventas: una fila por referencia_transaccion (No. de factura).
    Tomamos el primer movimiento de cada referencia para extraer fecha, usuario, estado.
    """
    qs = (
        Movimientos_Inventario_Sucursal.objects
        .filter(id_tipo_movimiento__codigo="VEN")
        .select_related("id_usuario", "estado_movimiento_inventario")
        .order_by("referencia_transaccion", "id")
    )

    ventas = []
    vistos = set()
    for m in qs:
        ref = m.referencia_transaccion or ""
        if ref in vistos:
            continue
        vistos.add(ref)
        ventas.append({
            "referencia": ref,
            "fecha": m.fecha_hora,
            "usuario": m.id_usuario,  # __str__ del modelo Usuario
            "estado": m.estado_movimiento_inventario,  # __str__ del estado
        })

    return render(request, "salidas/lista.html", {"ventas": ventas})

@login_required
def venta_detail(request, ref: str):
    movimientos = (
        Movimientos_Inventario_Sucursal.objects
        .filter(id_tipo_movimiento__codigo="VEN", referencia_transaccion=ref)
        .select_related("id_lote", "id_lote__id_producto", "id_usuario", "estado_movimiento_inventario")
        .order_by("id")
    )
    first = movimientos.first()
    return render(request, "salidas/partials/_consultar.html", {
        "referencia": ref,
        "fecha": first.fecha_hora if first else None,
        "usuario": first.id_usuario if first else "",
        "estado": first.estado_movimiento_inventario if first else "",
        "comentario": first.comentario if first else "",
        "movimientos": movimientos,
    })

@login_required
@transaction.atomic
def venta_create(request):
    if request.method == "GET":
        return render(
            request,
            "salidas/partials/form.html",
            {"now": timezone.localtime().strftime("%Y-%m-%dT%H:%M")},
        )

    # === Espera JSON ===
    try:
        data = json.loads((request.body or b"").decode("utf-8"))
    except Exception:
        return JsonResponse({"success": False, "errors": ["Payload inválido."]}, status=400)

    form_data = data.get("form_data") or {}
    detalles = data.get("detalles") or []

    ref = (form_data.get("numero_factura") or "").strip()
    comentario = (form_data.get("comentario") or "").strip()

    errors = []

    if not ref:
        errors.append("No. de factura requerido.")

    if not isinstance(detalles, list) or not detalles:
        errors.append("Debe agregar al menos un producto.")

    # tipo/estado requeridos
    tipo_ven = None
    estado_ok = None
    try:
        tipo_ven = Tipo_Movimiento_Inventario.objects.get(codigo="VEN")
    except Tipo_Movimiento_Inventario.DoesNotExist:
        errors.append("No existe el tipo de movimiento 'VEN'.")

    try:
        estado_ok = Estado_Movimiento_Inventario.objects.get(nombre_estado="Completado")
    except Estado_Movimiento_Inventario.DoesNotExist:
        errors.append("No existe el estado de movimiento 'Completado'.")

    # Validaciones por renglón y por producto (acumulado)
    # 1) estructura/numéricos
    clean_rows = []  # [(idx, producto: Productos, qty_int)]
    productos_reqs = {}  # producto_id -> qty_total_solicitada

    if detalles:
        for idx, det in enumerate(detalles, start=1):
            pid = det.get("producto_id")
            qty = det.get("cantidad")

            try:
                pid = int(pid)
            except Exception:
                pid = None

            try:
                qty = int(qty)
            except Exception:
                qty = 0

            if not pid:
                errors.append(f"Línea {idx}: producto inválido.")
                continue
            if qty <= 0:
                errors.append(f"Línea {idx}: cantidad inválida.")
                continue

            try:
                producto = Productos.objects.get(pk=pid)
            except Productos.DoesNotExist:
                errors.append(f"Línea {idx}: el producto (id={pid}) no existe.")
                continue

            clean_rows.append((idx, producto, qty))
            productos_reqs[pid] = productos_reqs.get(pid, 0) + qty

    # 2) stock suficiente por producto (suma de todos los lotes)
    if clean_rows:
        # inventario disponible por producto
        disponibles = (
            Lotes.objects
            .filter(id_producto_id__in=productos_reqs.keys(), cantidad_disponible__gt=0)
            .values("id_producto_id")
            .annotate(total=Sum("cantidad_disponible"))
        )
        disp_map = {r["id_producto_id"]: int(r["total"] or 0) for r in disponibles}

        for pid, qty_req in productos_reqs.items():
            total_disp = disp_map.get(pid, 0)
            if total_disp < qty_req:
                try:
                    nombre = Productos.objects.only("nombre").get(pk=pid).nombre
                except Productos.DoesNotExist:
                    nombre = f"ID {pid}"
                errors.append(
                    f"Stock insuficiente para '{nombre}'. Requerido: {qty_req}, disponible: {total_disp}."
                )

    if errors:
        return JsonResponse({"success": False, "errors": errors}, status=400)

    # === Si todo ok: aplicar FIFO y crear movimientos ===
    usuario = request.user

    try:
        for idx, producto, qty in clean_rows:
            restante = qty
            lotes = (
                Lotes.objects
                .filter(id_producto=producto, cantidad_disponible__gt=0)
                .order_by("fecha_caducidad", "id")
                .select_for_update()
            )

            for lote in lotes:
                if restante <= 0:
                    break
                disponible = int(lote.cantidad_disponible or 0)
                if disponible <= 0:
                    continue
                tomar = min(disponible, restante)

                # descuenta
                Lotes.objects.filter(pk=lote.pk).update(
                    cantidad_disponible=F("cantidad_disponible") - tomar
                )
                # movimiento (cantidad negativa por salida)
                Movimientos_Inventario_Sucursal.objects.create(
                    id_lote=lote,
                    id_tipo_movimiento=tipo_ven,
                    cantidad=-tomar,
                    id_usuario=usuario,
                    referencia_transaccion=ref,
                    comentario=comentario or None,
                    estado_movimiento_inventario=estado_ok,
                )
                restante -= tomar

            if restante > 0:
                # Esto no debería pasar por la pre-validación, pero por seguridad…
                raise ValueError(
                    f"Stock insuficiente para '{producto.nombre}'. Faltan {restante}."
                )

        return JsonResponse({"success": True})

    except ValueError as e:
        transaction.set_rollback(True)
        return JsonResponse({"success": False, "errors": [str(e)]}, status=400)
    except Exception:
        transaction.set_rollback(True)
        return JsonResponse({"success": False, "errors": ["Error interno al procesar la venta."]}, status=500)
