# apps/recepcion_almacenamiento/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required

from .models import Recepciones_Envio, Detalle_Recepcion
from apps.inventario.models import Lotes, Productos
from .forms import RecepcionForm
from django.db.models import Q
import json
from datetime import datetime


@login_required
def recepcion_list(request):
    recepciones = Recepciones_Envio.objects.select_related("id_usuario", "estado_recepcion")
    return render(request, "recepcion/lista.html", {"recepciones": recepciones})


@login_required
@transaction.atomic
def recepcion_create(request):
    if request.method == "POST":
        form = RecepcionForm(request.POST)
        detalles_json = request.POST.get("detalles_json")  # datos enviados en JSON desde el frontend

        if form.is_valid() and detalles_json:
            recepcion = form.save(commit=False)
            recepcion.id_usuario = request.user  # usuario logueado
            recepcion.save()

            detalles = json.loads(detalles_json)

            for d in detalles:
                producto_id = d.get("producto_id")
                numero_lote = d.get("lote")
                fecha_caducidad = d.get("fecha_caducidad")
                cantidad = int(d.get("cantidad"))
                costo = float(d.get("costo"))

                # Buscar o crear lote
                lote, creado = Lotes.objects.get_or_create(
                    id_producto_id=producto_id,
                    numero_lote=numero_lote,
                    defaults={
                        "fecha_caducidad": fecha_caducidad,
                        "cantidad_disponible": cantidad,
                    },
                )
                if not creado:
                    lote.cantidad_disponible += cantidad
                    lote.save()

                # Crear detalle de recepción
                Detalle_Recepcion.objects.create(
                    id_recepcion=recepcion,
                    id_lote=lote,
                    cantidad_recibida=cantidad,
                    costo_unitario=costo,
                )

            return JsonResponse({"success": True})

        return JsonResponse({"success": False, "errors": form.errors})

    else:
        form = RecepcionForm()
    return render(
        request,
        "recepcion/partials/_form.html",
        {"form": form, "action": "/recepcion_almacenamiento/crear/"},
    )


@login_required
def recepcion_detail(request, pk):
    recepcion = get_object_or_404(
        Recepciones_Envio.objects.select_related("id_usuario", "estado_recepcion"),
        pk=pk,
    )
    detalles = Detalle_Recepcion.objects.filter(id_recepcion=recepcion).select_related("id_lote")
    return render(
        request,
        "recepcion/partials/_consultar.html",
        {"recepcion": recepcion, "detalles": detalles},
    )

# Búsqueda de productos
@login_required
def search_productos(request):
    term = request.GET.get("term", "")
    productos = Productos.objects.filter(
        Q(nombre__icontains=term) | Q(codigo_producto__icontains=term)
    )[:20]  # limitar resultados

    results = [
        {
            "id": p.id,
            "codigo": p.codigo_producto,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "presentacion": getattr(p.id_presentacion, "nombre", ""),   # FK → Presentación
            "unidad": getattr(p.id_unidad_medida, "nombre", ""),       # FK → Unidad de medida
            "condicion": getattr(p.id_condicion_almacenamiento, "nombre", ""), # FK → Condición
            "receta": p.requiere_receta,
            "controlado": p.es_controlado,
        }
        for p in productos
    ]
    return JsonResponse(results, safe=False)


# Buscar Lotes
@login_required
def search_lotes(request, producto_id):
    term = request.GET.get("term", "").strip()
    qs = Lotes.objects.filter(id_producto_id=producto_id)

    if term:
        qs = qs.filter(numero_lote__icontains=term)

    lotes = qs.order_by("-id")[:20]  # trae los más recientes primero

    results = [
        {
            "id": l.id,
            "numero_lote": l.numero_lote,
            "fecha_caducidad": l.fecha_caducidad.strftime("%Y-%m-%d") if l.fecha_caducidad else "",
            "cantidad": l.cantidad_disponible,
        }
        for l in lotes
    ]
    return JsonResponse(results, safe=False)


# Crear Lotes
@login_required
def create_lote(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            producto_id = data.get("producto_id")
            numero      = data.get("numero_lote")
            caducidad   = data.get("fecha_caducidad") or None
            ubicacion   = data.get("ubicacion") or ""

            if not producto_id or not numero:
                return JsonResponse({"success": False, "error": "Datos incompletos."}, status=400)

            # Convertir fecha de string → date
            fecha_caducidad = None
            if caducidad:
                try:
                    fecha_caducidad = datetime.strptime(caducidad, "%Y-%m-%d").date()
                except ValueError:
                    return JsonResponse({"success": False, "error": "Formato de fecha inválido."}, status=400)

            lote = Lotes.objects.create(
                id_producto_id=producto_id,
                numero_lote=numero,
                fecha_caducidad=fecha_caducidad,
                cantidad_disponible=0,  # inicia en 0
                ubicacion_almacen=ubicacion,
                precio_compra=None,
                precio_venta=None,
                id_estado_lote_id=1,  # Pendiente por defecto
            )

            return JsonResponse({
                "success": True,
                "id": lote.id,
                "numero_lote": lote.numero_lote,
                "fecha_caducidad": lote.fecha_caducidad.strftime("%Y-%m-%d") if lote.fecha_caducidad else "",
            })

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
        
