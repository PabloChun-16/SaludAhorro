import io
import json
from datetime import datetime as dt

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import Solicitudes_Faltantes, Detalle_Solicitud_Faltantes
from apps.mantenimiento.models import Usuario, Estado_Solicitud
from apps.inventario.models import Productos
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string


@login_required
def solicitud_cambiar_estado_modal(request, id):
    solicitud = get_object_or_404(Solicitudes_Faltantes, pk=id)
    # Sólo estos 3 estados
    estados = Estado_Solicitud.objects.filter(
        nombre_estado__in=["Enviada", "Completada", "Cancelada"]
    ).order_by("nombre_estado")

    html = render_to_string(
        "solicitudes_bodega_central/partials/cambiar_estado.html",
        {
            "solicitud": solicitud,
            "estados": estados,
            "actual": solicitud.id_estado_solicitud.nombre_estado if solicitud.id_estado_solicitud else "",
        },
        request=request,
    )
    return JsonResponse({"html": html})


@login_required
@require_POST
@transaction.atomic
def solicitud_cambiar_estado(request, id):
    solicitud = get_object_or_404(Solicitudes_Faltantes, pk=id)
    estado_id = request.POST.get("estado_id")
    try:
        estado = Estado_Solicitud.objects.get(pk=estado_id)
    except Estado_Solicitud.DoesNotExist:
        return JsonResponse({"success": False, "error": "Estado inválido."}, status=400)

    solicitud.id_estado_solicitud = estado
    solicitud.save(update_fields=["id_estado_solicitud"])
    return JsonResponse({"success": True})


# ==============================
# HOME
# ==============================
@login_required
def index(request):
    return render(request, "solicitudes_bodega_central/index.html")


# ==============================
# REGISTRO / LISTADO PRINCIPAL
# ==============================
@login_required
def registrar_solicitud(request):
    solicitudes = (
        Solicitudes_Faltantes.objects
        .select_related("id_usuario", "id_estado_solicitud")
        .prefetch_related("detalles__id_producto")
        .order_by("-fecha_solicitud")
    )

    context = {
        "solicitudes": solicitudes,
        "productos": Productos.objects.all(),
        "usuarios": Usuario.objects.all(),
        "estados": Estado_Solicitud.objects.all(),
    }
    # 👇 Aquí tienes TODO tu HTML de registrar embebido (tal como pediste)
    return render(request, "solicitudes_bodega_central/registrar.html", context)


# ==============================
# BUSCADOR AJAX DE PRODUCTOS
# ==============================
@login_required
def buscar_productos(request):
    """
    Devuelve JSON para el buscador del input en registrar.html.
    Query: ?q=texto
    Respuesta: [{id, nombre, codigo, presentacion, stock}]
    """
    q = (request.GET.get("q") or "").strip()
    qs = Productos.objects.all()
    if q:
        try:
            from django.db.models import Q
            qs = qs.filter(
                Q(nombre__icontains=q) |
                Q(codigo__icontains=q) |
                Q(codigo_barras__icontains=q)
            )
        except Exception:
            qs = qs.filter(nombre__icontains=q)

    def safe_attr(obj, field, default=""):
        try:
            v = getattr(obj, field, default)
            return v if v is not None else default
        except Exception:
            return default

    data = []
    for p in qs[:30]:
        data.append({
            "id": p.id,
            "nombre": safe_attr(p, "nombre"),
            "codigo": safe_attr(p, "codigo", safe_attr(p, "codigo_barras", "")),
            "presentacion": safe_attr(getattr(p, "id_presentacion", None), "nombre", ""),
            # si no tienes stock en este modelo, mandamos 0 para que el front no falle
            "stock": 0,
        })
    return JsonResponse(data, safe=False)


# ==============================
# CREAR SOLICITUD (POST JSON)
# ==============================
@login_required
@transaction.atomic
def crear_solicitud(request):
    # Evita el 405 si entran por GET directo
    if request.method != "POST":
        return redirect("solicitudes_bodega_central:registrar_solicitud")

    try:
        payload = json.loads((request.body or b"").decode("utf-8"))
    except Exception:
        return JsonResponse({"success": False, "errors": "Payload inválido."}, status=400)

    form_data = payload.get("form_data") or {}
    detalles = payload.get("detalles") or []

    nombre_documento = (form_data.get("nombre_documento") or "").strip()
    comentario = (form_data.get("comentario") or "").strip()

    if not nombre_documento:
        return JsonResponse({"success": False, "errors": "El nombre del documento es requerido."}, status=400)
    if not detalles:
        return JsonResponse({"success": False, "errors": "Debe agregar al menos un producto."}, status=400)

    # Usuario (tu app usa modelo Usuario)
    usuario = get_object_or_404(Usuario, id=request.user.id)

    # Estado inicial
    estado = Estado_Solicitud.objects.filter(nombre_estado__iexact="Enviada").first()
    if not estado:
        estado = get_object_or_404(Estado_Solicitud, id=1)

    # Crear cabecera
    solicitud = Solicitudes_Faltantes.objects.create(
        nombre_documento=nombre_documento,
        fecha_solicitud=timezone.now(),
        id_estado_solicitud=estado,
        id_usuario=usuario,
    )

    # Crear renglones
    try:
        for idx, d in enumerate(detalles, start=1):
            pid = d.get("producto_id")
            qty = d.get("cantidad")
            urgente = bool(d.get("urgente"))
            obs = (d.get("observaciones") or "").strip() or None

            try:
                qty = int(qty)
            except Exception:
                qty = 0

            if not pid or qty <= 0:
                raise ValueError(f"Producto/cantidad inválidos en la línea {idx}.")

            # valida existencia
            get_object_or_404(Productos, pk=pid)

            Detalle_Solicitud_Faltantes.objects.create(
                id_solicitud=solicitud,
                id_producto_id=pid,
                cantidad_solicitada=qty,
                es_urgente=urgente,
                observaciones=obs,
            )

        return JsonResponse({"success": True})

    except ValueError as e:
        transaction.set_rollback(True)
        return JsonResponse({"success": False, "errors": str(e)}, status=400)
    except Exception:
        transaction.set_rollback(True)
        return JsonResponse({"success": False, "errors": "Error interno al guardar la solicitud."}, status=500)


# ==============================
# EDITAR
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

            if detalle:
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
# ELIMINAR
# ==============================
@login_required
def eliminar_solicitud(request, id):
    solicitud = get_object_or_404(Solicitudes_Faltantes, id=id)
    if request.method == "POST":
        solicitud.delete()
    return redirect("solicitudes_bodega_central:registrar_solicitud")


# ==============================
# OBTENER (si lo usas desde un modal)
# ==============================
@login_required
def obtener_solicitud(request, id):
    solicitud = get_object_or_404(Solicitudes_Faltantes, id=id)
    detalle = solicitud.detalles.first()

    data = {
        "documento": solicitud.nombre_documento,
        "producto": detalle.id_producto.nombre if detalle else "",
        "cantidad": detalle.cantidad_solicitada if detalle else "",
        "urgente": "Sí" if (detalle and detalle.es_urgente) else "No",
        "observaciones": (detalle.observaciones if (detalle and detalle.observaciones) else "—"),
        "estado": solicitud.id_estado_solicitud.nombre_estado if solicitud.id_estado_solicitud else "",
    }
    return JsonResponse(data)


# ==============================
# LISTAR
# ==============================
@login_required
def listar_solicitudes(request):
    solicitudes = (
        Solicitudes_Faltantes.objects
        .select_related("id_estado_solicitud", "id_usuario")
        .prefetch_related("detalles__id_producto")
        .order_by("-fecha_solicitud")
    )

    solicitudes_json = [
        {
            "documento": s.nombre_documento,
            "producto": s.detalles.first().id_producto.nombre if s.detalles.first() else "",
            "usuario": getattr(s.id_usuario, "nombre", str(s.id_usuario)),
            "estado": s.id_estado_solicitud.nombre_estado if s.id_estado_solicitud else "",
            "fecha": s.fecha_solicitud.strftime("%Y-%m-%d"),
        }
        for s in solicitudes
    ]

    return render(
        request,
        "solicitudes_bodega_central/listar.html",
        {"solicitudes": solicitudes, "solicitudes_json": json.dumps(solicitudes_json, cls=DjangoJSONEncoder)},
    )


# ==============================
# PDF
# ==============================
@login_required
def exportar_solicitudes_pdf(request):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))

    styles = getSampleStyleSheet()
    elementos = []

    header = Table(
        [[
            Paragraph("<b>Reporte de Solicitudes · SAIF</b>", styles["Heading2"]),
            Paragraph(dt.now().strftime("%d/%m/%Y %H:%M"), styles["Normal"]),
        ]],
        colWidths=[450, 100],
    )
    header.setStyle(TableStyle([("ALIGN", (1, 0), (1, 0), "RIGHT")]))
    elementos.append(header)
    elementos.append(Spacer(1, 12))

    data = [["Documento", "Producto", "Cantidad", "Urgente", "Observaciones", "Estado", "Fecha"]]

    solicitudes = (
        Solicitudes_Faltantes.objects
        .select_related("id_estado_solicitud")
        .prefetch_related("detalles__id_producto")
        .order_by("-fecha_solicitud")
    )

    for s in solicitudes:
        d = s.detalles.first()
        if d:
            data.append([
                s.nombre_documento or "",
                d.id_producto.nombre if d.id_producto else "",
                d.cantidad_solicitada or "",
                "Sí" if d.es_urgente else "No",
                d.observaciones or "—",
                s.id_estado_solicitud.nombre_estado if s.id_estado_solicitud else "",
                s.fecha_solicitud.strftime("%d/%m/%Y %H:%M") if s.fecha_solicitud else "",
            ])

    tabla = Table(data, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(14/255, 122/255, 58/255)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elementos.append(tabla)
    doc.build(elementos)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="reporte_solicitudes.pdf")
