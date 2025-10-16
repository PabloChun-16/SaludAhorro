from django.shortcuts import render

def index(request):
    return render(request, "alertas_vencimientos/index.html")