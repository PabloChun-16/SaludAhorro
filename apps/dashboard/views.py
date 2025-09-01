from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    return HttpResponse("Dashboard privado")

def index(request):
    return HttpResponse("dashboard OK - Prueba GIT")

def prueba(request):
    return HttpResponse("Prueba solo para Probar el GIT")