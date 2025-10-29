from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from .forms import RecetaForm
from .models import (
    EstadoEnvioReceta,
    RecetaMedica,
    EnvioReceta,
    DetalleEnvioReceta,   # del MODELO
    Producto,
    Usuario,
)

from datetime import datetime
import io
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from django.db import connection


@login_required
@require_http_methods(["GET", "POST"])
def envio_cambiar_estado(request, pk):
    """
    GET  -> devuelve JSON {html: "<form ...>"} con el modal para cambiar estado
    POST -> cambia el estado y devuelve JSON {success: True/False, error?}
    """
    envio = get_object_or_404(
        EnvioReceta.objects.select_related("id_estado_envio"),
        pk=pk
    )

    if request.method == "POST":
        estado_id = request.POST.get("estado_id")
        try:
            estado = get_object_or_404(EstadoEnvioReceta, pk=estado_id)
            envio.id_estado_envio = estado
            envio.save(update_fields=["id_estado_envio"])
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e) or "No se pudo actualizar."})

    # GET -> render del modal como html embebido en JSON
    estados = EstadoEnvioReceta.objects.all().order_by("nombre_estado")
    html = render_to_string(
        "recetas/partials/envio_cambiar_estado_modal.html",
        {"envio": envio, "estados": estados},
        request=request,
    )
    return JsonResponse({"html": html})

# ================================
#           RECETAS
# ================================

def index(request):
    return render(request, "recetas/index.html")


@login_required
def registrar_receta(request):
    """
    Vista principal que renderiza el HTML con tabla, filtros y modales de Recetas.
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
    Lista “aparte” (si la usas para dashboard/reportes).
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
    Modal 'Crear' -> POST a esta ruta.
    """
    if request.method == "POST":
        form = RecetaForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("recetas:registrar_receta")


@login_required
def editar_receta(request, pk):
    """
    Modal 'Editar' -> POST a /recetas/<pk>/editar/
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
    Modal 'Eliminar' -> POST a /recetas/<pk>/eliminar/
    """
    if request.method == "POST":
        receta = get_object_or_404(RecetaMedica, pk=pk)
        receta.delete()
    return redirect("recetas:registrar_receta")


@login_required
def detalle_receta(request, pk):
    """
    Vista dedicada (si alguna vez navegas fuera del modal).
    """
    receta = get_object_or_404(
        RecetaMedica.objects.select_related("id_producto", "id_usuario_venta"),
        pk=pk
    )
    return render(request, "recetas/detalle_receta.html", {"receta": receta})


@login_required
def consultar_receta(request, receta_id):
    """
    Endpoint alternativo para consultar receta (si decides cargar por fetch/iframe).
    """
    receta = get_object_or_404(
        RecetaMedica.objects.select_related("id_producto", "id_usuario_venta"),
        pk=receta_id
    )
    return render(request, "recetas/detalle_receta.html", {"receta": receta})


@login_required
def exportar_recetas_pdf(request):
    """
    Reporte PDF estilo SAIF (Recetas).
    """
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
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.0, 0.494, 0.224)),  # verde SAIF
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
#     BUSCADOR DE FACTURAS (AJAX)
# ================================
@login_required
def search_facturas(request):
    """
    Facturas (referencia_transaccion) provenientes de
    salidas_devoluciones_movimientos_inventario_sucursal con tipo VEN (id=4/codigo='VEN')
    y estado 'Completado'. Devuelve 1 fila por factura (la más reciente).
    """
    term = (request.GET.get("term") or "").strip()

    # 1) Intentar resolver el ID de 'Completado' de manera segura.
    def get_estado_completado_id(default=2):
        try:
            with connection.cursor() as cur:
                cur.execute("""
                    SELECT id
                    FROM mantenimiento_estado_movimiento_inventario
                    WHERE LOWER(nombre_estado) = 'completado'
                    LIMIT 1
                """)
                row = cur.fetchone()
                if row:
                    return row[0]
        except Exception:
            # La tabla puede no existir o tener otro nombre. Usamos default.
            pass
        return default

    estado_completado_id = get_estado_completado_id()

    # 2) Consulta. Nota: evitamos JOIN a la tabla de estado para no depender del nombre.
    sql = """
        SELECT DISTINCT ON (m.referencia_transaccion)
               m.referencia_transaccion                                 AS factura,
               to_char(m.fecha_hora, 'DD/MM/YYYY HH24:MI')              AS fecha,
               p.id                                                     AS producto_id,
               COALESCE(p.nombre, '')                                   AS producto_nombre
        FROM salidas_devoluciones_movimientos_inventario_sucursal m
        JOIN mantenimiento_tipo_movimiento_inventario t
             ON t.id = m.id_tipo_movimiento_id
        LEFT JOIN inventario_lotes l
             ON l.id = m.id_lote_id
        LEFT JOIN inventario_productos p
             ON p.id = l.id_producto_id
        WHERE (t.id = 4 OR UPPER(t.codigo) = 'VEN')
          AND m.estado_movimiento_inventario_id = %s
          AND m.referencia_transaccion IS NOT NULL
          AND (
                %s = '' OR
                m.referencia_transaccion ILIKE %s OR
                COALESCE(p.nombre, '') ILIKE %s
              )
        ORDER BY m.referencia_transaccion, m.fecha_hora DESC
        LIMIT 50
    """
    like = f"%{term}%"
    params = [estado_completado_id, term, like, like]

    rows = []
    with connection.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    # 3) Formato esperado por tu front (usuario lo dejamos vacío si no está en la consulta).
    results = [
        {
            "factura": r[0],
            "usuario_id": None,
            "usuario_nombre": "",
            "producto_id": r[2],
            "producto_nombre": r[3],
            "fecha": r[1],
        }
        for r in rows
        if (r[0] or "").strip()  # sanity check
    ]

    return JsonResponse(results, safe=False)


# ================================
#            ENVÍOS
# ================================

@login_required
def registrar_envio(request):
    """
    Pantalla principal de Envíos: Tabla de envíos + modal crear/editar/consultar.
    """
    envios = (
        EnvioReceta.objects
        .select_related("id_usuario", "id_estado_envio")
        .order_by("-fecha_envio")
    )
    # Para buscadores en el modal (recetas)
    recetas = (
        RecetaMedica.objects
        .select_related("id_producto", "id_usuario_venta")
        .order_by("-fecha_venta")
    )
    return render(request, "recetas/registrar_envio.html", {
        "envios": envios,
        "usuarios": Usuario.objects.all(),                 # si decides mostrar en algún lado
        "estados": EstadoEnvioReceta.objects.all(),        # idem
        "recetas": recetas,
    })


@login_required
def crear_envio(request):
    if request.method == "POST":
        nombre_reporte = request.POST.get("nombre_reporte", "").strip()
        recetas_ids = [rid for rid in request.POST.getlist("recetas[]") if rid]

        # 1) Estado "Enviado" (crea si no existe)
        estado_enviado, _ = EstadoEnvioReceta.objects.get_or_create(
            nombre_estado="Enviado"
        )

        # 2) Usuario del envío (automático)
        usuario_envio = None
        if recetas_ids:
            # Toma el usuario de la primera receta seleccionada
            r0 = RecetaMedica.objects.select_related("id_usuario_venta").filter(pk=recetas_ids[0]).first()
            if r0 and r0.id_usuario_venta_id:
                usuario_envio = r0.id_usuario_venta

        # 3) Crear el envío principal (solo una vez)
        envio = EnvioReceta.objects.create(
            fecha_envio=timezone.now(),
            nombre_reporte=nombre_reporte,
            id_estado_envio=estado_enviado,
            id_usuario=usuario_envio,
        )

        # 4) Crear los detalles de las recetas asociadas
        for rid in recetas_ids:
            DetalleEnvioReceta.objects.create(id_envio=envio, id_receta_id=rid)

        # 5) Redirigir tras crear
        return redirect("recetas:registrar_envio")

    # Si no es POST, simplemente redirige o muestra el formulario
    return redirect("recetas:registrar_envio")

@login_required
def editar_envio(request, pk):
    """
    Edita encabezado de Envío.
    - Mantiene el estado en "Enviado" (lo fuerza).
    - Usuario del envío no se edita manualmente (se ignoran campos si vienen del form).
    - Si envías fecha_envio en el form, se actualiza.
    """
    envio = get_object_or_404(EnvioReceta, pk=pk)

    if request.method == "POST":
        envio.nombre_reporte = (request.POST.get("nombre_reporte") or "").strip()

        # Forzar estado "Enviado"
        estado_enviado, _ = EstadoEnvioReceta.objects.get_or_create(nombre_estado="Enviado")
        envio.id_estado_envio = estado_enviado

        # Ignorar cambios manuales de usuario; si quisieras recalcular por detalle, hazlo aquí.

        fecha_envio = request.POST.get("fecha_envio")
        if fecha_envio:
            # Django convierte str a datetime si field es DateTimeField con USE_TZ; de lo contrario haz parse
            envio.fecha_envio = fecha_envio

        envio.save()

    return redirect("recetas:registrar_envio")


@login_required
def eliminar_envio(request, pk):
    """
    Elimina Envío (encabezado + detalles por cascade si el modelo lo define).
    """
    if request.method == "POST":
        envio = get_object_or_404(EnvioReceta, pk=pk)
        envio.delete()
    return redirect("recetas:registrar_envio")


@login_required
def lista_envios(request):
    """
    Lista detallada (para reporte o vista dedicada) usando DetalleEnvioReceta,
    de modo que aparezcan TODAS las recetas asociadas a cada envío.
    """
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
        .order_by("-id_envio__fecha_envio", "id_envio_id", "id_receta_id")
    )
    return render(request, "recetas/lista_envios.html", {"detalles": detalles})

@login_required
def recetas_por_envio(request, envio_id):
    """
    Retorna en formato JSON todas las recetas asociadas a un envío.
    """
    detalles = (
        DetalleEnvioReceta.objects
        .select_related("id_receta", "id_receta__id_producto", "id_receta__id_usuario_venta")
        .filter(id_envio_id=envio_id)
    )

    data = []
    for d in detalles:
        r = d.id_receta
        data.append({
            "factura": r.referencia_factura or "",
            "referente": r.referente_receta or "",
            "producto": r.id_producto.nombre if r.id_producto else "",
            "usuario": r.id_usuario_venta.nombre if r.id_usuario_venta else "",
            "fecha": r.fecha_venta.strftime("%d/%m/%Y %H:%M") if r.fecha_venta else "",
        })
    return JsonResponse(data, safe=False)

@login_required
def exportar_envios_pdf(request):
    """
    Reporte PDF detallado de Envíos (incluye recetas por envío).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("<b>Reporte de Detalles de Envíos · SAIF</b>", styles["Title"]))
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), styles["Normal"]))
    elementos.append(Spacer(1, 20))

    data = [["Reporte", "Estado", "Usuario Envío", "Fecha Envío", "Factura Receta", "Producto"]]

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
