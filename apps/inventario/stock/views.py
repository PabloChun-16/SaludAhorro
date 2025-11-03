from django.shortcuts import render, get_object_or_404
from django.http import FileResponse
from django.db.models import Q              # ⬅️ nuevo
from apps.inventario.models import Lotes
import io
from django.utils.html import escape
from django.utils.timezone import now
from datetime import datetime               # ⬅️ nuevo

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from apps.inventario.models import Productos
from django.http import JsonResponse
from django.db.models import Sum

from apps.mantenimiento.models import Estado_Lote

# ---------- helpers PDF ----------
def _register_fonts():
    # intenta cargar DejaVuSans si existe en static/fonts, si no usa Helvetica
    try:
        from django.conf import settings
        import os
        font_path = os.path.join(settings.BASE_DIR, "static", "fonts", "DejaVuSans.ttf")
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("DejaVu", font_path))
            return "DejaVu"
    except Exception:
        pass
    return "Helvetica"


def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = landscape(A4)
    canvas.setFillColorRGB(0.054, 0.478, 0.227)  # #0E7A3A
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(24, h - 18, "Reporte de Stock · SAIF")
    canvas.setFont("Helvetica", 9)
    canvas.setFillColorRGB(0.25, 0.25, 0.25)
    canvas.drawRightString(w - 24, h - 18, now().strftime("%d/%m/%Y %H:%M"))
    canvas.setFont("Helvetica", 9)
    canvas.setFillColorRGB(0.35, 0.35, 0.35)
    canvas.drawRightString(w - 24, 16, f"Página {doc.page}")
    canvas.restoreState()


# =============== LISTA ===============
def stock_list(request):
    lotes = (
        Lotes.objects
        .select_related("id_producto", "id_producto__id_presentacion", "id_estado_lote")
        .all()
    )

    estados_unicos = (
        Estado_Lote.objects
        .values_list("nombre_estado", flat=True)
        .order_by("nombre_estado")
        .distinct()
    )

    return render(request, "stock/lista.html", {
        "lotes": lotes,
        "estados_unicos": estados_unicos
    })


# =============== DETALLE ===============
def stock_detail(request, pk):
    lote = get_object_or_404(
        Lotes.objects.select_related("id_producto", "id_producto__id_presentacion", "id_estado_lote"),
        pk=pk,
    )
    return render(request, "stock/partials/_consultar.html", {"lote": lote})


# =============== EXPORTAR PDF (con filtros) ===============
def exportar_stock_pdf(request):
    """
    Exporta el PDF respetando los filtros que llegan por querystring desde la UI:
    - codigo, nombre, desc, pres, lote
    - cadu_desde (yyyy-mm-dd), cadu_hasta (yyyy-mm-dd)
    - estado: "", "vigente", "vencido", "otros"
    - solo_disponibles: "1" para incluir únicamente lotes con stock > 0
    """
    # ---- Leer filtros ----
    codigo = (request.GET.get("codigo") or "").strip()
    nombre = (request.GET.get("nombre") or "").strip()
    desc   = (request.GET.get("desc") or "").strip()
    pres   = (request.GET.get("pres") or "").strip()
    lote   = (request.GET.get("lote") or "").strip()
    cadu_desde = (request.GET.get("cadu_desde") or "").strip()
    cadu_hasta = (request.GET.get("cadu_hasta") or "").strip()
    estado = (request.GET.get("estado") or "").strip().lower()
    solo_disponibles = request.GET.get("solo_disponibles") == "1"

    qs = (
        Lotes.objects
        .select_related("id_producto", "id_producto__id_presentacion", "id_estado_lote")
        .all()
    )

    # ---- Aplicar filtros en queryset ----
    if codigo:
        qs = qs.filter(id_producto__codigo_producto__icontains=codigo)
    if nombre:
        qs = qs.filter(id_producto__nombre__icontains=nombre)
    if desc:
        qs = qs.filter(id_producto__descripcion__icontains=desc)
    if pres:
        qs = qs.filter(id_producto__id_presentacion__nombre_presentacion__icontains=pres)
    if lote:
        # `Lotes` model uses `numero_lote` as the DB field. Avoid querying
        # non-existent `codigo_lote` field (some older code/templates
        # referenced it). Use `numero_lote` only.
        qs = qs.filter(Q(numero_lote__icontains=lote))

    # rango de caducidad
    def parse_date(d):
        try:
            return datetime.strptime(d, "%Y-%m-%d").date()
        except Exception:
            return None

    d1 = parse_date(cadu_desde)
    d2 = parse_date(cadu_hasta)
    if d1:
        qs = qs.filter(fecha_caducidad__gte=d1)
    if d2:
        qs = qs.filter(fecha_caducidad__lte=d2)

    if estado:
        if estado in ("vigente", "vencido"):
            qs = qs.filter(id_estado_lote__nombre_estado__iexact=estado.capitalize())
        elif estado == "otros":
            qs = qs.exclude(id_estado_lote__nombre_estado__in=["Vigente", "Vencido"])

    if solo_disponibles:
        qs = qs.filter(cantidad_disponible__gt=0)

    # ---- Construcción del PDF ----
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=18, rightMargin=18,
        topMargin=36, bottomMargin=28,
        title="Reporte de Stock",
    )

    font_name = _register_fonts()
    styles = getSampleStyleSheet()
    p8_left   = ParagraphStyle("p8_left",   parent=styles["Normal"], fontName=font_name, fontSize=8, leading=10, alignment=TA_LEFT)
    p8_center = ParagraphStyle("p8_center", parent=styles["Normal"], fontName=font_name, fontSize=8, leading=10, alignment=TA_CENTER)
    p8_right  = ParagraphStyle("p8_right",  parent=styles["Normal"], fontName=font_name, fontSize=8, leading=10, alignment=TA_RIGHT)
    hdr_style = ParagraphStyle("hdr", parent=styles["Normal"], fontName=font_name, fontSize=9, leading=11, alignment=TA_CENTER, textColor=colors.whitesmoke)

    headers = ["Código", "Producto", "Descripción", "Presentación", "Disp.",
               "Lote", "Vencimiento", "Estado Lote", "P. Compra", "P. Venta"]
    data = [[Paragraph(escape(h), hdr_style) for h in headers]]

    def cell(text, style):
        return Paragraph(escape(text or ""), style)

    def money(val):
        if val is None:
            return ""
        try:
            return f"Q {float(val):,.2f}"
        except (TypeError, ValueError):
            return ""

    for lote_obj in qs:
        prod   = lote_obj.id_producto
        pres_o = getattr(prod, "id_presentacion", None)
        estado_o = lote_obj.id_estado_lote

        codigo_v = getattr(prod, "codigo_producto", "") if prod else ""
        nombre_v = getattr(prod, "nombre", "") if prod else ""
        desc_v   = getattr(prod, "descripcion", "") or ""
        presentacion_v = getattr(pres_o, "nombre_presentacion", "") if pres_o else ""
        disp_v   = lote_obj.cantidad_disponible or 0
        # Use numero_lote as canonical value; `codigo_lote` is provided
        # via a compatibility property on the model if needed.
        nro_v    = getattr(lote_obj, "numero_lote", "") or ""
        venc_v   = lote_obj.fecha_caducidad.strftime("%d/%m/%Y") if getattr(lote_obj, "fecha_caducidad", None) else ""
        est_v    = getattr(estado_o, "nombre_estado", "") if estado_o else ""
        pcomp_v  = money(lote_obj.precio_compra)
        pvent_v  = money(lote_obj.precio_venta)

        data.append([
            cell(codigo_v, p8_center),
            cell(nombre_v, p8_left),
            cell(desc_v, p8_left),
            cell(presentacion_v, p8_left),
            cell(str(disp_v), p8_center),
            cell(nro_v, p8_center),
            cell(venc_v, p8_center),
            cell(est_v, p8_center),
            cell(pcomp_v, p8_right),
            cell(pvent_v, p8_right),
        ])

    # ---- Anchos proporcionales al ancho útil (evita cortes) ----
    total_w = doc.width
    ratios = [
        0.08,  # Código
        0.15,  # Producto
        0.15,  # Descripción
        0.12,  # Presentación
        0.06,  # Disp.
        0.10,  # Lote
        0.09,  # Vencimiento
        0.08,  # Estado Lote
        0.08,  # P. Compra
        0.08,  # P. Venta
    ]
    col_widths = [total_w * r for r in ratios]

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0E7A3A")),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),

        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),

        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fa")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cfd8dc")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#0E7A3A")),
    ]))

    doc.build([Spacer(1, 4), table], onFirstPage=_header_footer, onLaterPages=_header_footer)
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename="reporte_stock.pdf")


# =============== REPORTE STOCK CRÍTICO (JSON) ===============
def reporte_stock_critico(request):
    # Sumar stock disponible por producto
    productos = (
        Productos.objects
        .annotate(stock_total=Sum("lotes__cantidad_disponible"))
        .filter(stock_total__lte=5)  # límite configurable
        .values("codigo_producto", "nombre", "stock_total")
    )

    data = list(productos)
    return JsonResponse(data, safe=False)
