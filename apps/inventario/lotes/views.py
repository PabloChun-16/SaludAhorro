from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models import ProtectedError
from django.views.decorators.http import require_POST
from apps.inventario.models import Lotes
from apps.mantenimiento.models import Estado_Lote

# ---------- helper: lista de relaciones que impiden eliminar ----------
def _relaciones_que_bloquean(lote: Lotes):
    """
    Revisa TODAS las relaciones reversas del lote (FK/OneToOne) y devuelve
    una lista con los nombres de los modelos que tienen registros vinculados.
    No requiere conocer los nombres de modelos de recepciones/salidas, etc.
    """
    detalles = []
    for rel in lote._meta.related_objects:
        if not (rel.one_to_many or rel.one_to_one):
            continue
        accessor = rel.get_accessor_name()
        try:
            manager = getattr(lote, accessor)
        except Exception:
            continue

        try:
            if rel.one_to_one:
                # Si no existe, lanza DoesNotExist
                manager  # tocarlo para que evalue
                detalles.append(rel.related_model._meta.verbose_name.title())
            else:
                if manager.exists():
                    detalles.append(rel.related_model._meta.verbose_name_plural.title())
        except Exception:
            # No hay relación existente (p.ej. OneToOne vacío)
            pass

    return detalles

def _puede_eliminar(lote: Lotes):
    atados = _relaciones_que_bloquean(lote)
    if atados:
        razon = "No se puede eliminar porque tiene registros asociados: " + ", ".join(atados)
        return False, razon
    return True, ""

# ---------- lista ----------
def lista_lotes(request):
    lotes = Lotes.objects.select_related("id_producto", "id_estado_lote").all()
    return render(request, "lotes/lista.html", {"lotes": lotes})

# ---------- consultar ----------
def consultar_lote(request, id):
    lote = get_object_or_404(Lotes, id=id)
    return render(request, "lotes/partials/_consultar.html", {"lote": lote})

# ---------- editar ----------
def editar_lote(request, id):
    lote = get_object_or_404(Lotes, id=id)
    estados = Estado_Lote.objects.all()
    if request.method == "POST":
        lote.fecha_caducidad = request.POST.get("fecha_caducidad")
        lote.ubicacion_almacen = request.POST.get("ubicacion_almacen")
        lote.id_estado_lote_id = request.POST.get("estado")
        lote.save()
        return JsonResponse({"success": True})
    return render(request, "lotes/partials/_form.html", {"lote": lote, "estados": estados})

# ---------- NUEVO: endpoint de pre-chequeo ----------
def puede_eliminar_lote(request, id):
    lote = get_object_or_404(Lotes, id=id)
    ok, reason = _puede_eliminar(lote)
    return JsonResponse({"allow": ok, "reason": reason})

# ---------- eliminar con verificación dura ----------
@require_POST
def eliminar_lote(request, id):
    lote = get_object_or_404(Lotes, id=id)
    ok, reason = _puede_eliminar(lote)
    if not ok:
        return JsonResponse({"success": False, "error": reason})
    lote.delete()
    return JsonResponse({"success": True})
