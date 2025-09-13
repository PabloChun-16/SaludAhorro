from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from apps.inventario.models import Lotes
import io
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


# Listado de lotes (Stock)
def stock_list(request):
    lotes = Lotes.objects.select_related("id_producto", "id_estado_lote").all()
    return render(request, "stock/lista.html", {"lotes": lotes})


# Consultar detalle de un lote (y su producto asociado)
def stock_detail(request, pk):
    lote = get_object_or_404(Lotes, pk=pk)
    return render(request, "stock/partials/_consultar.html", {"lote": lote})


# Exportar stock a PDF
def exportar_stock_pdf(request):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    # Cabecera de la tabla
    data = [["Código", "Producto", "Descripción", "Presentación", "Disponible",
             "Lote", "Vencimiento", "Estado Lote", "Precio Compra", "Precio Venta"]]

    # Cargar registros
    for lote in Lotes.objects.select_related("id_producto", "id_estado_lote").all():
        data.append([
            lote.id_producto.codigo_producto,
            lote.id_producto.nombre,
            lote.id_producto.descripcion,
            lote.id_producto.id_presentacion.nombre_presentacion if lote.id_producto.id_presentacion else "",
            lote.cantidad_disponible,
            lote.numero_lote,
            lote.fecha_caducidad.strftime("%d/%m/%Y"),
            lote.id_estado_lote.nombre_estado if lote.id_estado_lote else "",
            str(lote.precio_compra or ""),
            str(lote.precio_venta or ""),
        ])

    # Construcción de la tabla
    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b5e20")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    # Crear documento
    elements = [Paragraph("📦 Reporte de Stock", styles["Title"]), table]
    doc.build(elements)

    buffer.seek(0)
    return HttpResponse(buffer, content_type="application/pdf")
