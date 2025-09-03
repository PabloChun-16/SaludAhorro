from django.shortcuts import render
from django.shortcuts import render, HttpResponse


def index(request):
    return render(request, "mantenimiento/index.html")


def usuarios(request):
    return HttpResponse("Gestión de Usuarios")

def roles(request):
    return HttpResponse("Gestión de Roles")

def laboratorios(request):
    return HttpResponse("Gestión de Laboratorios")

def presentaciones(request):
    return HttpResponse("Gestión de Presentaciones")

def unidades_medida(request):
    return HttpResponse("Gestión de Unidades de Medida")

def condiciones_almacenamiento(request):
    return HttpResponse("Gestión de Condiciones de Almacenamiento")
