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
        # Solo render del formulario (lo cargas por fetch)
        # Si quieres pasar ahora=timezone.localtime() para precargar, hazlo aquí.
        return render(request, "salidas/partials/form.html", {"now": timezone.localtime().strftime("%Y-%m-%dT%H:%M")})

    # POST JSON
    try:
        data = json.loads((request.body or b"").decode("utf-8"))
    except Exception:
        return JsonResponse({"success": False, "errors": "Payload inválido."}, status=400)

    form_data = data.get("form_data", {}) or {}
    detalles = data.get("detalles", []) or []
    referencia = (form_data.get("numero_factura") or "").strip()
    # fecha_venta = form_data.get("fecha_venta")  # <- si tu modelo tiene auto_now_add, NO la uses aquí
    comentario = (form_data.get("comentario") or "").strip()

    if not referencia:
        return JsonResponse({"success": False, "errors": "No. de factura requerido."}, status=400)
    if not detalles:
        return JsonResponse({"success": False, "errors": "Debe agregar al menos un producto."}, status=400)

    # Busca tipo y estado
    try:
        tipo_ven = Tipo_Movimiento_Inventario.objects.get(codigo="VEN")
    except Tipo_Movimiento_Inventario.DoesNotExist:
        return JsonResponse({"success": False, "errors": "No existe el tipo de movimiento 'VEN'."}, status=400)

    try:
        estado_ok = Estado_Movimiento_Inventario.objects.get(nombre_estado="Completado")
    except Estado_Movimiento_Inventario.DoesNotExist:
        return JsonResponse({"success": False, "errors": "No existe el estado de movimiento 'Completado'."}, status=400)

    usuario = request.user

    # Procesar cada renglón con FIFO
    try:
        for idx, det in enumerate(detalles, start=1):
            pid = det.get("producto_id")
            qty = det.get("cantidad")
            try:
                qty = int(qty)
            except Exception:
                qty = 0

            if not pid or qty <= 0:
                raise ValueError(f"Producto/cantidad inválidos en línea {idx}.")

            producto = get_object_or_404(Productos, pk=pid)

            restante = qty
            # Lotes disponibles ordenados por caducidad (más próxima primero), nulos al final
            lotes = (
                Lotes.objects
                .filter(id_producto=producto, cantidad_disponible__gt=0)
                .order_by("fecha_caducidad", "id")
                .select_for_update()  # bloquea filas para FIFO correcto en concurrencia
            )

            for lote in lotes:
                if restante <= 0:
                    break

                disponible = int(lote.cantidad_disponible or 0)
                if disponible <= 0:
                    continue

                tomar = disponible if disponible <= restante else restante

                # Descontar del lote
                Lotes.objects.filter(pk=lote.pk).update(
                    cantidad_disponible=F("cantidad_disponible") - tomar
                )
                lote.refresh_from_db(fields=["cantidad_disponible"])

                # Registrar movimiento (cantidad NEGATIVA por salida)
                Movimientos_Inventario_Sucursal.objects.create(
                    id_lote=lote,
                    id_tipo_movimiento=tipo_ven,
                    cantidad=-tomar,
                    id_usuario=usuario,
                    referencia_transaccion=referencia,
                    comentario=comentario or None,
                    estado_movimiento_inventario=estado_ok,
                    # fecha_hora la deja el modelo (auto_now_add)
                )

                restante -= tomar

            if restante > 0:
                # No alcanzó el stock para esta línea
                raise ValueError(
                    f"Stock insuficiente para '{producto.nombre}'. Faltan {restante}."
                )

        return JsonResponse({"success": True})

    except ValueError as e:
        transaction.set_rollback(True)
        return JsonResponse({"success": False, "errors": str(e)}, status=400)
    except Exception as e:
        transaction.set_rollback(True)
        # Loguea e si quieres. Devuelvo mensaje genérico.
        return JsonResponse({"success": False, "errors": "Error interno al procesar la venta."}, status=500)
