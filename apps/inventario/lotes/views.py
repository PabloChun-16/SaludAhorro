from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db.models import ProtectedError
from apps.inventario.models import Lotes
from apps.mantenimiento.models import Estado_Lote
from datetime import datetime
from decimal import Decimal, InvalidOperation

# ---------------------------
# Utilidades de estados
# ---------------------------

def _estado_id(nombre: str) -> int:
    return Estado_Lote.objects.only("id").get(nombre_estado=nombre).id

def _permitidos_para_usuario_qs():
    # Solo "Disponible" y "En Cuarentena" se muestran en el <select>
    return Estado_Lote.objects.filter(nombre_estado__in=["Disponible", "En Cuarentena"]).order_by("nombre_estado")

# ---------------------------
# Reglas para "Retirar" (baja lógica)
# ---------------------------

def _razon_no_puede_retirar(lote: Lotes) -> str | None:
    # Stock debe ser exactamente 0
    if (lote.cantidad_disponible or 0) > 0:
        return "No puede retirarse: tiene stock disponible."

    # No permitir si ya está retirado o devuelto
    estado_actual = (lote.id_estado_lote.nombre_estado or "").strip().lower()
    if estado_actual in ("retirado", "devuelto"):
        return "Este lote ya no puede retirarse."

    return None  # OK

# ---------------------------
# Lista / Consultar / Editar
# ---------------------------

def lista_lotes(request):
    lotes = Lotes.objects.select_related("id_producto", "id_estado_lote").all()
    estados_unicos = Estado_Lote.objects.values_list("nombre_estado", flat=True).order_by("nombre_estado").distinct()
    return render(request, "lotes/lista.html", {"lotes": lotes, "estados_unicos": estados_unicos})

def consultar_lote(request, id):
    lote = get_object_or_404(Lotes, id=id)
    return render(request, "lotes/partials/_consultar.html", {"lote": lote})

def editar_lote(request, id):
    lote = get_object_or_404(Lotes, id=id)
    estados = _permitidos_para_usuario_qs()

    if request.method == "POST":
        def _parse_decimal(value_raw):
            if value_raw is None:
                return None
            value = value_raw.strip()
            if not value:
                return None

            normalized = value.replace(" ", "")
            if "," in normalized and "." in normalized:
                normalized = normalized.replace(",", "")
            elif "," in normalized and "." not in normalized:
                normalized = normalized.replace(",", ".")

            try:
                return Decimal(normalized)
            except (InvalidOperation, ValueError):
                raise ValueError

        # --- convertir fecha a objeto date ---
        fecha_caducidad_str = request.POST.get("fecha_caducidad")
        if fecha_caducidad_str:
            try:
                lote.fecha_caducidad = datetime.strptime(fecha_caducidad_str, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({
                    "success": False,
                    "error": "Formato de fecha inválido. Use AAAA-MM-DD."
                }, status=400)
        else:
            lote.fecha_caducidad = None

        lote.ubicacion_almacen = request.POST.get("ubicacion_almacen")
        precio_compra_raw = request.POST.get("precio_compra")
        precio_venta_raw = request.POST.get("precio_venta")
        try:
            lote.precio_compra = _parse_decimal(precio_compra_raw)
        except ValueError:
            return JsonResponse({"success": False, "error": "Precio de compra invalido. Use un valor numerico."}, status=400)
        try:
            lote.precio_venta = _parse_decimal(precio_venta_raw)
        except ValueError:
            return JsonResponse({"success": False, "error": "Precio de venta invalido. Use un valor numerico."}, status=400)

        # Validación de estado
        estado_post = request.POST.get("estado")
        try:
            estado_post = int(estado_post) if estado_post is not None else None
        except ValueError:
            estado_post = None

        permitidos_ids = set(estados.values_list("id", flat=True))
        if estado_post not in permitidos_ids:
            return JsonResponse({
                "success": False,
                "error": "Estado no permitido. Solo 'Disponible' o 'En Cuarentena'."
            }, status=400)

        lote.id_estado_lote_id = estado_post
        lote.save(update_fields=["fecha_caducidad", "ubicacion_almacen", "id_estado_lote", "precio_compra", "precio_venta"])
        return JsonResponse({"success": True})

    return render(request, "lotes/partials/_form.html", {"lote": lote, "estados": estados})
# ---------------------------
# Pre-chequeo y acción: RETIRAR
# ---------------------------

def puede_retirar_lote(request, id):
    lote = get_object_or_404(Lotes, id=id)
    reason = _razon_no_puede_retirar(lote)
    return JsonResponse({"allow": reason is None, "reason": reason or ""})

@require_POST
def retirar_lote(request, id):
    lote = get_object_or_404(Lotes, id=id)
    reason = _razon_no_puede_retirar(lote)
    if reason:
        return JsonResponse({"success": False, "error": reason}, status=400)

    retirado_id = _estado_id("Retirado")
    lote.id_estado_lote_id = retirado_id
    lote.save(update_fields=["id_estado_lote"])
    return JsonResponse({"success": True})
