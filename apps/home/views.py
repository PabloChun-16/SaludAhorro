from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return render(request, "home/index.html")

def blog(request):
    return render(request, "home/blog.html")

def contacto(request):
    return render(request, "home/contacto.html")

def nosotros(request):
    return render(request, "home/nosotros.html")

def saif(request):
    return render(request, "home/saif.html")

def login_view(request):
    return render(request, "home/login.html")
