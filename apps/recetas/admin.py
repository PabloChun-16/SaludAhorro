from django.contrib import admin
from .models import Recetas_Medicas, Envios_Recetas, Detalle_Envio_Recetas

# Register your models here.
admin.site.register(Recetas_Medicas)
admin.site.register(Envios_Recetas)
admin.site.register(Detalle_Envio_Recetas)
