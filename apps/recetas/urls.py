from django.urls import path
from . import views

app_name = 'recetas'

urlpatterns = [
    # Menú principal del módulo
    path('', views.index, name='index'),

    # CRUD de recetas
    path('registrar/', views.registrar_receta, name='registrar_receta'),
    path("detalle/<int:pk>/", views.detalle_receta, name="detalle_receta"), 
    path("lista/", views.lista_recetas, name="lista_recetas"),
    path("crear/", views.crear_receta, name="crear_receta"),
    path("<int:pk>/editar/", views.editar_receta, name="editar_receta"),
    path("<int:pk>/eliminar/", views.eliminar_receta, name="eliminar_receta"),
    path("<int:pk>/detalle/", views.detalle_receta, name="detalle_receta"),
    path("consultar/<int:receta_id>/", views.consultar_receta, name="consultar_receta"),
    path("exportar-pdf/", views.exportar_recetas_pdf, name="exportar_recetas_pdf"),
    
    # DRUD de envios
    path('registrar_envio/', views.registrar_envio, name='registrar_envio'),
    path("crear_envio/", views.crear_envio, name="crear_envio"),
    path("envio/<int:pk>/editar/", views.editar_envio, name="editar_envio"),
    path("envio/<int:pk>/eliminar/", views.eliminar_envio, name="eliminar_envio"),
    path('lista_envios/', views.lista_envios, name='lista_envios'),
    path("exportar-envios-pdf/", views.exportar_envios_pdf, name="exportar_envios_pdf"),
]