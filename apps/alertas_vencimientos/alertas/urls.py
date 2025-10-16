from django.urls import path
from . import views

app_name = "alertas"

urlpatterns = [
    path("", views.alertas_dashboard, name="alertas_dashboard"),
    path("stock_bajo/", views.alertas_stock_bajo, name="alertas_stock_bajo"),
    path("proximos_vencer/", views.alertas_proximos_vencer, name="alertas_proximos_vencer"),
    path("vencidos/", views.alertas_vencidos, name="alertas_vencidos"),
    path("agotamiento/", views.alertas_agotamiento, name="alertas_agotamiento"),
]
