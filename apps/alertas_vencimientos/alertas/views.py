from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.utils import timezone
from apps.inventario.models import Productos, Lotes


# -----------------------------------------------------------
# DASHBOARD PRINCIPAL DE ALERTAS
# -----------------------------------------------------------
@login_required
def alertas_dashboard(request):
    hoy = timezone.now().date()

    stock_bajo_count = (
        Productos.objects
        .annotate(stock_total=Coalesce(Sum('lotes__cantidad_disponible'), Value(0)))
        .filter(stock_minimo__gt=0, stock_total__lte=F('stock_minimo'))
        .count()
    )

    proximos_vencer_count = (
        Lotes.objects
        .filter(fecha_caducidad__range=[hoy, hoy + timedelta(days=30)], cantidad_disponible__gt=0)
        .count()
    )

    vencidos_count = (
        Lotes.objects
        .filter(fecha_caducidad__lt=hoy, cantidad_disponible__gt=0)
        .count()
    )

    agotamiento_count = _qs_agotamiento().count()

    return render(request, "alertas/lista.html", {
        "stock_bajo": stock_bajo_count,
        "proximos_vencer": proximos_vencer_count,
        "vencidos": vencidos_count,
        "agotamiento": agotamiento_count,
    })
# -----------------------------------------------------------
# DETALLES DE CADA REPORTE (MODALES)
# -----------------------------------------------------------

@login_required
def alertas_stock_bajo(request):
    # Productos cuyo stock_total <= stock_minimo (stock bajo)
    productos = (
        Productos.objects
        .annotate(stock_total=Coalesce(Sum('lotes__cantidad_disponible'), Value(0)))
        .filter(stock_minimo__isnull=False, stock_minimo__gt=0, stock_total__lte=F('stock_minimo'))
        .select_related('id_unidad_medida', 'id_presentacion')
    )

    return render(request, "alertas/partials/stock_bajo.html", {"productos": productos})
    
@login_required
def alertas_proximos_vencer(request):
    hoy = timezone.now().date()
    lotes = (
        Lotes.objects
        .select_related('id_producto')
        .filter(fecha_caducidad__range=[hoy, hoy + timedelta(days=30)], cantidad_disponible__gt=0)
        .order_by('fecha_caducidad')
    )

    # Agregar atributo dinámico 'dias_restantes' a cada lote para la plantilla
    for lote in lotes:
        try:
            lote.dias_restantes = (lote.fecha_caducidad - hoy).days
        except Exception:
            lote.dias_restantes = ""

    return render(request, "alertas/partials/proximos_vencer.html", {"lotes": lotes})



def _qs_agotamiento():
    """
    Productos cuyo stock_total <= 1.5 * stock_minimo.
    - stock_total = suma de lotes disponibles (coalesce a 0)
    - sólo considera productos con stock_minimo > 0
    """
    return (
        Productos.objects
        .annotate(
            stock_total=Coalesce(Sum('lotes__cantidad_disponible'), Value(0)),
        )
        .filter(
            stock_minimo__isnull=False,
            stock_minimo__gt=0,
            stock_total__lte=F('stock_minimo') * 2,
        )
        .select_related('id_unidad_medida', 'id_presentacion')
    )


@login_required
def alertas_agotamiento(request):
    """Devuelve el partial con los productos próximos a agotarse (misma lógica que alertas_stock_bajo)."""
    productos = _qs_agotamiento()
    # Calcular margen de agotamiento
    for p in productos:
        try:
            p.margen_porcentaje = round((p.stock_total / p.stock_minimo) * 100, 1)
        except ZeroDivisionError:
            p.margen_porcentaje = 0

    return render(request, "alertas/partials/agotamiento.html", {"productos": productos})


@login_required
def alertas_vencidos(request):
    hoy = timezone.now().date()
    lotes = (
        Lotes.objects
        .select_related('id_producto')
        .filter(fecha_caducidad__lt=hoy, cantidad_disponible__gt=0)
        .order_by('-fecha_caducidad')
    )
    return render(request, "alertas/partials/vencidos.html", {"lotes": lotes})
