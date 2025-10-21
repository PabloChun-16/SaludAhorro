from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from .forms import RecetaForm
from .models import (
    EstadoEnvioReceta,
    RecetaMedica,
    EnvioReceta,
    DetalleEnvioReceta,
    Producto,
    Usuario,
)

from datetime import datetime
import io
import json
from django.core.serializers.json import DjangoJSONEncoder


# ================================
#           RECETAS
# ================================

def index(request):
    return render(request, "recetas/index.html")


@login_required
def registrar_receta(request):
    """
    Vista principal que renderiza tu HTML 'todo-en-uno' con tabla y modales.
    """
    recetas = (
        RecetaMedica.objects
        .select_related("id_producto", "id_usuario_venta")
        .order_by("-fecha_venta")
    )
    productos = Producto.objects.all()
    usuarios = Usuario.objects.all()

    return render(request, "recetas/registrar_receta.html", {
        "recetas": recetas,
        "productos": productos,
        "usuarios": usuarios,
        "form": RecetaForm(),
    })


@login_required
def lista_recetas(request):
    """
    Lista aparte (si la necesitas).
    """
    recetas = RecetaMedica.objects.select_related("id_producto", "id_usuario_venta").all()
    recetas_json = [
        {
            "id": r.id,
            "factura": r.referencia_factura or "",
            "referente": r.referente_receta or "",
            "producto": r.id_producto.nombre if r.id_producto else "",
            "usuario": r.id_usuario_venta.nombre if r.id_usuario_venta else "",
            "fecha": r.fecha_venta.strftime("%Y-%m-%d %H:%M") if r.fecha_venta else "",
        }
        for r in recetas
    ]
    return render(request, "recetas/lista_recetas.html", {
        "recetas": recetas,
        "recetas_json": json.dumps(recetas_json, cls=DjangoJSONEncoder),
    })


@login_required
def crear_receta(request):
    """
    El modal 'Crear' hace POST a esta ruta.
    """
    if request.method == "POST":
        form = RecetaForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("recetas:registrar_receta")


@login_required
def editar_receta(request, pk):
    """
    El modal 'Editar' envía POST a /recetas/<pk>/editar/
    """
    receta = get_object_or_404(RecetaMedica, pk=pk)
    if request.method == "POST":
        form = RecetaForm(request.POST, instance=receta)
        if form.is_valid():
            form.save()
    return redirect("recetas:registrar_receta")


@login_required
def eliminar_receta(request, pk):
    """
    El modal 'Eliminar' envía POST a /recetas/<pk>/eliminar/
    """
    if request.method == "POST":
        receta = get_object_or_404(RecetaMedica, pk=pk)
        receta.delete()
    return redirect("recetas:registrar_receta")


@login_required
def detalle_receta(request, pk):
    receta = get_object_or_404(
        RecetaMedica.objects.select_related("id_producto", "id_usuario_venta"),
        pk=pk
    )
    return render(request, "recetas/detalle_receta.html", {"receta": receta})


@login_required
def consultar_receta(request, receta_id):
    receta = get_object_or_404(
        RecetaMedica.objects.select_related("id_producto", "id_usuario_venta"),
        pk=receta_id
    )
    return render(request, "recetas/detalle_receta.html", {"receta": receta})


@login_required
def exportar_recetas_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="reporte_recetas.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []

    styles = getSampleStyleSheet()
    header = Table(
        [[Paragraph("<b>Reporte de Recetas · SAIF</b>", styles["Heading2"]),
          Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), styles["Normal"])]],
        colWidths=[450, 100]
    )
    header.setStyle(TableStyle([("ALIGN", (1, 0), (1, 0), "RIGHT")]))
    elements.append(header)
    elements.append(Spacer(1, 12))

    data = [["Factura", "Referente", "Producto", "Usuario Venta", "Fecha"]]
    recetas = RecetaMedica.objects.select_related("id_producto", "id_usuario_venta").all()
    for r in recetas:
        data.append([
            r.referencia_factura or "",
            r.referente_receta or "",
            r.id_producto.nombre if r.id_producto else "",
            r.id_usuario_venta.nombre if r.id_usuario_venta else "",
            r.fecha_venta.strftime("%d/%m/%Y %H:%M") if r.fecha_venta else "",
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.0, 0.494, 0.224)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)
    return response


# ================================
#            ENVÍOS
# ================================

@login_required
def registrar_envio(request):
    envios = (
        EnvioReceta.objects
        .select_related("id_usuario", "id_estado_envio")
        .order_by("-fecha_envio")
    )
    return render(request, "recetas/registrar_envio.html", {
        "envios": envios,
        "usuarios": Usuario.objects.all(),
        "estados": EstadoEnvioReceta.objects.all(),
        # Para el modal de búsqueda local:
        "recetas": RecetaMedica.objects.select_related("id_producto", "id_usuario_venta").all(),
    })


@login_required
def crear_envio(request):
    if request.method == "POST":
        envio = EnvioReceta.objects.create(
            fecha_envio=timezone.now(),
            nombre_reporte=request.POST.get("nombre_reporte"),
            id_estado_envio_id=request.POST.get("id_estado_envio"),
            id_usuario_id=request.POST.get("id_usuario"),
        )

        # Detalle (IDs enviados como recetas[])
        recetas_ids = request.POST.getlist("recetas[]")
        for rid in recetas_ids:
            if rid:
                DetalleEnvioReceta.objects.create(id_envio=envio, id_receta_id=rid)

        return redirect("recetas:registrar_envio")

    # Si entran por GET, redirige a registrar envíos
    return redirect("recetas:registrar_envio")


@login_required
def editar_envio(request, pk):
    envio = get_object_or_404(EnvioReceta, pk=pk)
    if request.method == "POST":
        envio.nombre_reporte = request.POST.get("nombre_reporte")
        envio.id_estado_envio_id = request.POST.get("id_estado_envio")
        envio.id_usuario_id = request.POST.get("id_usuario")
        fecha_envio = request.POST.get("fecha_envio")
        if fecha_envio:
            # Si viene como 'YYYY-MM-DDTHH:MM', Django lo parsea al asignar si es DateTimeField; si no, conviene parsear.
            try:
                envio.fecha_envio = datetime.fromisoformat(fecha_envio)
            except Exception:
                envio.fecha_envio = envio.fecha_envio  # deja como estaba si falla el parseo
        envio.save()
    return redirect("recetas:registrar_envio")


@login_required
def eliminar_envio(request, pk):
    if request.method == "POST":
        envio = get_object_or_404(EnvioReceta, pk=pk)
        envio.delete()
    return redirect("recetas:registrar_envio")


@login_required
def lista_envios(request):
    detalles = (
        DetalleEnvioReceta.objects
        .select_related(
            "id_envio",
            "id_envio__id_usuario",
            "id_envio__id_estado_envio",
            "id_receta",
            "id_receta__id_producto",
            "id_receta__id_usuario_venta",
        )
        .all()
    )
    return render(request, "recetas/lista_envios.html", {"detalles": detalles})


@login_required
def exportar_envios_pdf(request):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("<b>Reporte de Detalles de Envíos · SAIF</b>", styles["Title"]))
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), styles["Normal"]))
    elementos.append(Spacer(1, 20))

    data = [["Reporte", "Estado", "Usuario", "Fecha", "Receta", "Producto"]]

    detalles = DetalleEnvioReceta.objects.select_related(
        "id_envio", "id_envio__id_estado_envio", "id_envio__id_usuario",
        "id_receta", "id_receta__id_producto"
    ).all()

    for d in detalles:
        data.append([
            d.id_envio.nombre_reporte or "",
            d.id_envio.id_estado_envio.nombre_estado if d.id_envio.id_estado_envio else "",
            d.id_envio.id_usuario.nombre if d.id_envio.id_usuario else "",
            d.id_envio.fecha_envio.strftime("%d/%m/%Y %H:%M") if d.id_envio.fecha_envio else "",
            d.id_receta.referencia_factura if d.id_receta else "",
            d.id_receta.id_producto.nombre if d.id_receta and d.id_receta.id_producto else "",
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.055, 0.478, 0.227)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (0, 1), (-1, -1), "LEFT"),
    ]))

    elementos.append(table)
    doc.build(elementos)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="detalle_envios.pdf")
