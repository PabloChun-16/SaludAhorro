# apps/inventario/management/commands/actualizar_estados_lotes.py
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from apps.inventario.models import Lotes
from apps.mantenimiento.models import Estado_Lote


def ensure_estado(nombre, descripcion=""):
    obj, _ = Estado_Lote.objects.get_or_create(
        nombre_estado=nombre,
        defaults={"descripcion": descripcion},
    )
    return obj.id


class Command(BaseCommand):
    help = "Actualiza automáticamente los estados de los lotes según la fecha de caducidad."

    def handle(self, *args, **options):
        hoy = timezone.localdate()
        dias = int(getattr(settings, "PROXIMO_VENCER_DIAS", 30))
        limite_proximo = hoy + timedelta(days=dias)

        # Asegura que existan los estados necesarios y obtén sus IDs
        id_disponible = ensure_estado("Disponible", "El lote está listo para su venta o uso.")
        id_cuarentena = ensure_estado("En Cuarentena", "El lote está en revisión y no está disponible para su uso.")
        id_vencido    = ensure_estado("Vencido", "El lote ha caducado y debe ser retirado.")
        id_proximo    = ensure_estado("Próximo a Vencer", "El lote está dentro de un rango de tiempo definido para caducar.")
        id_retirado   = ensure_estado("Retirado", "Baja lógica del inventario.")
        id_devuelto   = ensure_estado("Devuelto", "Devuelto al proveedor.")

        # 1) Marcar VENCIDOS: fecha_caducidad < hoy (sin tocar retirados/devueltos)
        q1 = Lotes.objects.filter(
            fecha_caducidad__lt=hoy
        ).exclude(
            id_estado_lote_id__in=[id_retirado, id_devuelto]
        )
        vencidos = q1.exclude(id_estado_lote_id=id_vencido).update(id_estado_lote_id=id_vencido)

        # 2) Marcar PRÓXIMO A VENCER: hoy <= fecha_caducidad <= limite
        q2 = Lotes.objects.filter(
            fecha_caducidad__gte=hoy,
            fecha_caducidad__lte=limite_proximo,
        ).exclude(
            id_estado_lote_id__in=[id_vencido, id_retirado, id_devuelto]
        )
        proximos = q2.exclude(id_estado_lote_id=id_proximo).update(id_estado_lote_id=id_proximo)

        # 3) Quitar “Próximo a vencer” si ya no está en ventana y volver a Disponible
        # (no tocamos Cuarentena ni Retirado/Devuelto)
        q3 = Lotes.objects.filter(
            id_estado_lote_id=id_proximo,
            fecha_caducidad__gt=limite_proximo,
        )
        revertidos = q3.update(id_estado_lote_id=id_disponible)

        self.stdout.write(self.style.SUCCESS(
            f"Estados actualizados: vencidos={vencidos}, proximos={proximos}, revertidos_a_disponible={revertidos}"
        ))
