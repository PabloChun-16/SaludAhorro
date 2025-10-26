# apps/inventario/signals.py
from datetime import timedelta
from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from apps.inventario.models import Lotes
from apps.mantenimiento.models import Estado_Lote

PROX_VENCER_DIAS = getattr(settings, "PROXIMO_VENCER_DIAS", 30)
AUTO_ESTADOS = {"Vencido", "Próximo a Vencer"}          # los que maneja el sistema
ESTADOS_FUERTES = {"Retirado", "Devuelto"}              # nunca tocarlos automáticamente

# Caché simple en memoria de ids por nombre (evita hits repetidos a BD)
_estado_id_cache = {}
def estado_id(nombre: str) -> int:
    if nombre not in _estado_id_cache:
        _estado_id_cache[nombre] = Estado_Lote.objects.only("id").get(nombre_estado=nombre).id
    return _estado_id_cache[nombre]

def calcular_estado_por_fecha(fecha_caducidad):
    if not fecha_caducidad:
        return None
    hoy = timezone.localdate()
    if fecha_caducidad < hoy:
        return "Vencido"
    if fecha_caducidad <= hoy + timedelta(days=PROX_VENCER_DIAS):
        return "Próximo a Vencer"
    return None

@receiver(pre_save, sender=Lotes)
def lotes_auto_estado_por_fecha(sender, instance: Lotes, **kwargs):
    """
    Reglas:
      - Si el estado actual es Retirado o Devuelto → no tocar.
      - Si la fecha indica Vencido o Próximo a Vencer → forzar ese estado.
      - Si la fecha NO cae en esas ventanas y el estado actual era uno de los
        auto-manejados (Vencido / Próximo a Vencer) → devolver a 'Disponible'
        (o dejar el que el usuario eligió: Disponible / En Cuarentena).
    """
    estado_actual = (getattr(instance.id_estado_lote, "nombre_estado", "") or "").strip()
    if estado_actual in ESTADOS_FUERTES:
        return  # no tocar

    auto = calcular_estado_por_fecha(instance.fecha_caducidad)

    if auto in AUTO_ESTADOS:
        instance.id_estado_lote_id = estado_id(auto)
        return

    # Si ya no aplica auto-estado y el actual era uno "auto", vuélvelo a Disponible.
    if estado_actual in AUTO_ESTADOS:
        instance.id_estado_lote_id = estado_id("Disponible")
        return

    # Si el usuario eligió Disponible o En Cuarentena, respétalo.
    # (No hacer nada aquí).
