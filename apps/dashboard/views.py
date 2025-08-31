from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return HttpResponse("dashboard OK - Prueba GIT")

def prueba(request):
    return HttpResponse("Prueba solo para Probar el GIT")