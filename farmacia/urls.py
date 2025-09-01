"""
URL configuration for farmacia project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
    

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.home.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('accounts/', include('apps.accounts.urls')),

    path('ajustes_inventario/', include('apps.ajustes_inventario.urls')),
    path('alertas_vencimientos/', include('apps.alertas_vencimientos.urls')),
    path('recepcion_almacenamiento/', include('apps.recepcion_almacenamiento.urls')),
    path('recetas/', include('apps.recetas.urls')),
    path('salidas_devoluciones/', include('apps.salidas_devoluciones.urls')),
    path('solicitudes_bodega_central/', include('apps.solicitudes_bodega_central.urls')),
]
