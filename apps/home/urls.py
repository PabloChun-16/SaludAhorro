from django.urls import path
from . import views

app_name = "home"  # sirve para namespacing en plantillas {% url 'home:index' %}

urlpatterns = [
    path("", views.index, name="index"),
    path("blog/", views.blog, name="blog"),
    path("contacto/", views.contacto, name="contacto"),
    path("nosotros/", views.nosotros, name="nosotros"),
    path("saif/", views.saif, name="saif"),
    path("login/", views.login_view, name="login"),
]
