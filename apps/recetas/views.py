from django.http import FileResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import  DetalleEnvioReceta
from .models import EstadoEnvioReceta, RecetaMedica, EnvioReceta, DetalleEnvioReceta, Producto, Usuario
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from .forms import RecetaForm
from django.utils import timezone
from datetime import datetime
import io




# Vista principal (menú del módulo de recetas)
def index(request):
    return render(request, 'recetas/index.html')

def detalle_receta(request, pk):
    receta = get_object_or_404(RecetaMedica, pk=pk)
    return render(request, "recetas/detalle_receta.html", {"receta": receta})

# Registrar receta médica
def registrar_receta(request):
    recetas = RecetaMedica.objects.all().order_by("-fecha_venta")
    productos = Producto.objects.all()
    usuarios = Usuario.objects.all()
    form = RecetaForm()

    return render(request, "recetas/registrar_receta.html", {
        "recetas": recetas,
        "productos": productos,
        "usuarios": usuarios,
        "form": form
    })
    
# Listado de recetas
def lista_recetas(request):
    recetas = RecetaMedica.objects.select_related("id_producto", "id_usuario_venta").all()
    return render(request, "recetas/lista_recetas.html", {"recetas": recetas})

def crear_receta(request):
    if request.method == "POST":
        form = RecetaForm(request.POST)
        if form.is_valid():
            receta = form.save(commit=False)
            receta.fecha_venta = timezone.now()
            receta.save()
            return redirect("recetas:registrar_receta")

def editar_receta(request, pk):
    receta = get_object_or_404(RecetaMedica, pk=pk)

    if request.method == "POST":
        form = RecetaForm(request.POST, instance=receta)  
        if form.is_valid():
            form.save()
            return redirect("recetas:registrar_receta")  
    return redirect("recetas:registrar_receta")

def eliminar_receta(request, pk):
    receta = get_object_or_404(RecetaMedica, pk=pk)
    receta.delete()
    return redirect("recetas:registrar_receta")

# Consultar receta (AJAX)
def consultar_receta(request, receta_id):
    receta = get_object_or_404(RecetaMedica.objects.select_related("id_producto", "id_usuario_venta"), pk=receta_id)
    return render(request, "recetas/detalle_receta.html", {"receta": receta})

# Exportar a PDF
def exportar_recetas_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="reporte_recetas.pdf"'

    # Documento horizontal
    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []

    # Estilos
    styles = getSampleStyleSheet()

    # Encabezado: Título y fecha
    header = Table([
        [Paragraph("<b>Reporte de Recetas · SAIF</b>", styles["Heading2"]),
         Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), styles["Normal"])]
    ], colWidths=[450, 100])
    header.setStyle(TableStyle([("ALIGN", (1, 0), (1, 0), "RIGHT")]))
    elements.append(header)
    elements.append(Spacer(1, 12))

    # Encabezados de tabla
    data = [["Factura", "Referente", "Producto", "Usuario Venta", "Fecha"]]

    # Datos de recetas
    recetas = RecetaMedica.objects.select_related("id_producto", "id_usuario_venta").all()
    for r in recetas:
        data.append([
            r.referencia_factura or "",
            r.referente_receta or "",
            r.id_producto.nombre if r.id_producto else "",
            r.id_usuario_venta.nombre if r.id_usuario_venta else "",
            r.fecha_venta.strftime("%d/%m/%Y %H:%M"),
        ])

    # Tabla con estilo tipo inventario
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#007E33")),  # Verde cabecera
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)

    # Construcción del PDF
    doc.build(elements)
    return response

# =============================
#           ENVÍOS
# =============================

# Registrar envío de recetas
def registrar_envio(request):
    envios = EnvioReceta.objects.select_related("id_usuario", "id_estado_envio").all()
    return render(request, "recetas/registrar_envio.html", {
        "envios": envios,
        "usuarios": Usuario.objects.all(),
        "estados": EstadoEnvioReceta.objects.all(),
        "recetas": RecetaMedica.objects.all(),
    })

def crear_envio(request):
    if request.method == "POST":
        # Crear cabecera del envío
        envio = EnvioReceta.objects.create(
            fecha_envio=timezone.now(),
            nombre_reporte=request.POST.get("nombre_reporte"),
            id_estado_envio_id=request.POST.get("id_estado_envio"),
            id_usuario_id=request.POST.get("id_usuario")
        )

        # Guardar recetas asociadas (detalle)
        recetas_ids = request.POST.getlist("recetas[]")  # viene del formulario (checkboxes, inputs ocultos, etc.)
        for rid in recetas_ids:
            DetalleEnvioReceta.objects.create(
                id_envio=envio,
                id_receta_id=rid
            )

        return redirect("recetas:lista_envios")

    recetas = RecetaMedica.objects.all()
    return render(request, "recetas/registrar_envio.html", {"recetas": recetas})

def editar_envio(request, pk):
    envio = get_object_or_404(EnvioReceta, pk=pk)
    if request.method == "POST":
        envio.nombre_reporte = request.POST.get("nombre_reporte")
        envio.id_estado_envio_id = request.POST.get("id_estado_envio")
        envio.id_usuario_id = request.POST.get("id_usuario")
        envio.fecha_envio = request.POST.get("fecha_envio")
        envio.save()
        return redirect("recetas:registrar_envio")
    return render(request, "recetas/editar_envio.html", {"envio": envio})


def eliminar_envio(request, pk):
    envio = get_object_or_404(EnvioReceta, pk=pk)
    if request.method == "POST":
        envio.delete()
        return redirect("recetas:registrar_envio")
    return render(request, "recetas/eliminar_envio.html", {"envio": envio})

# =============================
# LISTA DE DETALLES DE ENVÍOS
# =============================
def lista_envios(request):
    detalles = (
        DetalleEnvioReceta.objects
        .select_related(
            "id_envio",            # Relación con EnvioRecetas
            "id_envio__id_usuario",
            "id_envio__id_estado_envio",
            "id_receta",           # Relación con Recetas
            "id_receta__id_producto",
            "id_receta__id_usuario_venta"
        )
        .all()
    )

    return render(request, "recetas/lista_envios.html", {
        "detalles": detalles
    })

# =============================
# EXPORTAR DETALLES DE ENVÍOS A PDF
# =============================
def exportar_envios_pdf(request):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Estilos
    styles = getSampleStyleSheet()
    elementos = []

    # Encabezado
    encabezado = Paragraph("<b>Reporte de Detalles de Envíos · SAIF</b>", styles["Title"])
    fecha_gen = Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), styles["Normal"])

    elementos.append(encabezado)
    elementos.append(Spacer(1, 12))
    elementos.append(fecha_gen)
    elementos.append(Spacer(1, 20))

    # Encabezados de tabla
    data = [[
        "Reporte", "Estado", "Usuario", "Fecha", "Receta", "Producto"
    ]]

    # Datos
    detalles = DetalleEnvioReceta.objects.select_related(
        "id_envio", "id_envio__id_estado_envio", "id_envio__id_usuario",
        "id_receta", "id_receta__id_producto"
    ).all()

    for d in detalles:
        data.append([
            d.id_envio.nombre_reporte,
            d.id_envio.id_estado_envio.nombre_estado,   # aquí usamos el nombre correcto
            d.id_envio.id_usuario.nombre,
            d.id_envio.fecha_envio.strftime("%d/%m/%Y %H:%M"),
            d.id_receta.referencia_factura,
            d.id_receta.id_producto.nombre,
        ])

    # Crear tabla
    table = Table(data, repeatRows=1)

    # Estilos de la tabla
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(14/255, 122/255, 58/255)),  # Verde SAIF
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (0, 1), (-1, -1), "LEFT"),
    ])
    table.setStyle(style)

    elementos.append(table)

    # Generar PDF
    doc.build(elementos)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="detalle_envios.pdf")