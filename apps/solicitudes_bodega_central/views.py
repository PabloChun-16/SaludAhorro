import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from .models import Solicitudes_Faltantes, Detalle_Solicitud_Faltantes
from apps.mantenimiento.models import Usuario
from apps.inventario.models import Productos
from apps.mantenimiento.models import Estado_Solicitud
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
import datetime
from django.http import FileResponse
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import io
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def index(request):
    return render(request, "solicitudes_bodega_central/index.html")

# ==============================
# REGISTRO / LISTADO PRINCIPAL
# ==============================
def registrar_solicitud(request):
    solicitudes = Solicitudes_Faltantes.objects.select_related(
        "id_usuario", "id_estado_solicitud"
    ).prefetch_related("detalles__id_producto").order_by("-fecha_solicitud")

    context = {
        "solicitudes": solicitudes,
        "productos": Productos.objects.all(),
        "usuarios": Usuario.objects.all(),
        "estados": Estado_Solicitud.objects.all(),
    }
    return render(request, "solicitudes_bodega_central/registrar.html", context)


# ==============================
# CREAR SOLICITUD
# ==============================
@login_required
def crear_solicitud(request):
    if request.method == "POST":
        try:
            usuario = get_object_or_404(Usuario, id=request.user.id)

            # Estado inicial: "Enviada"
            estado_inicial = get_object_or_404(Estado_Solicitud, id=1)

            # Crear la solicitud principal
            solicitud = Solicitudes_Faltantes.objects.create(
                nombre_documento=request.POST.get("nombre_documento"),
                fecha_solicitud=timezone.now(),
                id_estado_solicitud=estado_inicial,
                id_usuario=usuario,
            )

            # Registrar detalles (pueden ser varios productos)
            productos = request.POST.getlist("id_producto[]")
            cantidades = request.POST.getlist("cantidad_solicitada[]")
            urgentes = request.POST.getlist("es_urgente[]")
            observaciones = request.POST.getlist("observaciones[]")

            for i in range(len(productos)):
                if not productos[i] or not cantidades[i]:
                    continue
                Detalle_Solicitud_Faltantes.objects.create(
                    id_solicitud=solicitud,
                    id_producto_id=productos[i],
                    cantidad_solicitada=cantidades[i],
                    es_urgente=(str(i) in urgentes or urgentes[i] == "on"),
                    observaciones=observaciones[i],
                )

        except Exception as e:
            messages.error(request, f"❌ Error al registrar la solicitud: {e}")
            return redirect("solicitudes_bodega_central:registrar_solicitud")

    return redirect("solicitudes_bodega_central:registrar_solicitud")


# ==============================
# EDITAR SOLICITUD
# ==============================
@login_required
def editar_solicitud(request, id):
    solicitud = get_object_or_404(Solicitudes_Faltantes, id=id)
    detalle = solicitud.detalles.first()

    if request.method == "POST":
        try:
            solicitud.nombre_documento = request.POST.get("nombre_documento")
            solicitud.id_estado_solicitud_id = request.POST.get("id_estado_solicitud")
            solicitud.save()

            detalle.id_producto_id = request.POST.get("id_producto")
            detalle.cantidad_solicitada = request.POST.get("cantidad_solicitada")
            detalle.observaciones = request.POST.get("observaciones")
            detalle.save()

        except Exception as e:
            messages.error(request, f"❌ Error al actualizar la solicitud: {e}")

        return redirect("solicitudes_bodega_central:registrar_solicitud")

    productos = Productos.objects.all()
    estados = Estado_Solicitud.objects.all()
    return render(
        request,
        "solicitudes_bodega_central/registrar.html",
        {"solicitud": solicitud, "detalle": detalle, "productos": productos, "estados": estados},
    )


# ==============================
# ELIMINAR SOLICITUD
# ==============================
@login_required
def eliminar_solicitud(request, id):
    solicitud = get_object_or_404(Solicitudes_Faltantes, id=id)
    if request.method == "POST":
        solicitud.delete()
    return redirect("solicitudes_bodega_central:registrar_solicitud")


# ==============================
#  OBTENER DETALLE (para modal)
# ==============================
@login_required
def obtener_solicitud(request, id):
    solicitud = get_object_or_404(Solicitudes_Faltantes, id=id)
    detalle = solicitud.detalles.first()

    data = {
        "documento": solicitud.nombre_documento,
        "producto": detalle.id_producto.nombre,
        "cantidad": detalle.cantidad_solicitada,
        "urgente": "Sí" if detalle.es_urgente else "No",
        "observaciones": detalle.observaciones or "—",
        "estado": solicitud.id_estado_solicitud.nombre_estado,
    }
    return render(request, "solicitudes_bodega_central/partials/detalle.html", data)


# =======================
#   LISTAR SOLICITUDES
# =======================
def listar_solicitudes(request):
    solicitudes = (
        Solicitudes_Faltantes.objects
        .select_related("id_estado_solicitud", "id_usuario")
        .prefetch_related("detalles__id_producto")
        .all()
        .order_by("-fecha_solicitud")
    )

    solicitudes_json = [
        {
            "documento": s.nombre_documento,
            "producto": s.detalles.first().id_producto.nombre if s.detalles.first() else "",
            "usuario": s.id_usuario.nombre,
            "estado": s.id_estado_solicitud.nombre_estado,
            "fecha": s.fecha_solicitud.strftime("%Y-%m-%d"),
        }
        for s in solicitudes
    ]

    return render(request, "solicitudes_bodega_central/listar.html", {
        "solicitudes": solicitudes,
        "solicitudes_json": json.dumps(solicitudes_json, cls=DjangoJSONEncoder),
    })

# =======================
#   EXPORTAR A PDF (SAIF)
# =======================
def exportar_solicitudes_pdf(request):
    """
    Genera un PDF con el listado de solicitudes al estilo SAIF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))

    # Estilos SAIF
    styles = getSampleStyleSheet()
    elementos = []

    # ===================== ENCABEZADO =====================
    header = Table([
        [
            Paragraph("<b>Reporte de Solicitudes · SAIF</b>", styles["Heading2"]),
            Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), styles["Normal"])
        ]
    ], colWidths=[450, 100])
    header.setStyle(TableStyle([("ALIGN", (1, 0), (1, 0), "RIGHT")]))
    elementos.append(header)
    elementos.append(Spacer(1, 12))

    # ===================== TABLA =====================
    data = [["Documento", "Producto", "Cantidad", "Urgente", "Observaciones", "Estado", "Fecha"]]

    solicitudes = Solicitudes_Faltantes.objects.select_related("id_estado_solicitud").prefetch_related("detalles").all()

    for s in solicitudes:
        detalle = s.detalles.first()
        if detalle:
            data.append([
                s.nombre_documento or "",
                detalle.id_producto.nombre if detalle.id_producto else "",
                detalle.cantidad_solicitada or "",
                "Sí" if detalle.es_urgente else "No",
                detalle.observaciones or "—",
                s.id_estado_solicitud.nombre_estado if s.id_estado_solicitud else "",
                s.fecha_solicitud.strftime("%d/%m/%Y %H:%M") if s.fecha_solicitud else "",
            ])

    # ===================== ESTILOS DE TABLA =====================
    tabla = Table(data, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(14/255, 122/255, 58/255)),  # Verde SAIF
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elementos.append(tabla)

    # ===================== CONSTRUIR PDF =====================
    doc.build(elementos)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="reporte_solicitudes.pdf")