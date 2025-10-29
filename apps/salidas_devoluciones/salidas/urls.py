from django.urls import path
from . import views

app_name = "salidas"

urlpatterns = [

    path("<str:ref>/exportar/", views.venta_export_pdf, name="venta_export_pdf"), 

    
    path("", views.venta_list, name="list"),                 # ✅ nombre correcto (sin “s”)
    path("crear/", views.venta_create, name="create"),
    path("detalle/<str:ref>/", views.venta_detail, name="detail"),
     path("cancelar/<str:ref>/", views.venta_cancel, name="cancel"),
       
]
