from django.urls import path, include
from . import views

app_name = "alertas_vencimientos"

urlpatterns = [
    path("", views.index, name="index"),
   path(
       "vencimientos/",
       include(("apps.alertas_vencimientos.vencimientos.urls", "vencimientos"),
               namespace="vencimientos")
   ),
   path("alertas/",
        include(("apps.alertas_vencimientos.alertas.urls", "alertas"), 
                namespace="alertas")
    ),    
]
