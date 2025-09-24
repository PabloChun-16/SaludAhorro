from django.urls import path
from . import views

app_name = "stock"

urlpatterns = [
    path("", views.stock_list, name="lista"),
    path("<int:pk>/consultar/", views.stock_detail, name="consultar"),
    path("exportar/pdf/", views.exportar_stock_pdf, name="exportar_pdf"),
    path("reporte/stock-critico/", views.reporte_stock_critico, name="reporte_stock_critico"),

]
