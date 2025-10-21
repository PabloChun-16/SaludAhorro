from django.urls import path
from . import views

app_name = "recetas"

urlpatterns = [
    # ==============================
    #        MENÚ PRINCIPAL
    # ==============================
    path("", views.index, name="index"),

    # ==============================
    #           RECETAS
    # ==============================
    path("registrar/", views.registrar_receta, name="registrar_receta"),
    path("lista/", views.lista_recetas, name="lista_recetas"),
    path("crear/", views.crear_receta, name="crear_receta"),
    path("<int:pk>/editar/", views.editar_receta, name="editar_receta"),
    path("<int:pk>/eliminar/", views.eliminar_receta, name="eliminar_receta"),
    path("<int:pk>/detalle/", views.detalle_receta, name="detalle_receta"),
    path("consultar/<int:receta_id>/", views.consultar_receta, name="consultar_receta"),
    path("exportar-pdf/", views.exportar_recetas_pdf, name="exportar_recetas_pdf"),

    # ==============================
    #             ENVÍOS
    # ==============================
    path("envios/registrar/", views.registrar_envio, name="registrar_envio"),
    path("envios/crear/", views.crear_envio, name="crear_envio"),

    # rutas usadas por JS
    path("envio/<int:pk>/editar/", views.editar_envio, name="editar_envio"),
    path("envio/<int:pk>/eliminar/", views.eliminar_envio, name="eliminar_envio"),

    # ==============================
    #          ALIASES EXTRA
    # ==============================
    # Compatibilidad con enlaces escritos a mano o viejos
    path("registrar_envio/", views.registrar_envio),   # /recetas/registrar_envio/
    path("crear_envio/", views.crear_envio),           # /recetas/crear_envio/
    path("lista_envios/", views.lista_envios),         # /recetas/lista_envios/ ✅ nuevo alias

    # Plurales antiguos
    path("envios/<int:pk>/editar/", views.editar_envio),
    path("envios/<int:pk>/eliminar/", views.eliminar_envio),

    path("envios/lista/", views.lista_envios, name="lista_envios"),
    path("envios/exportar-pdf/", views.exportar_envios_pdf, name="exportar_envios_pdf"),
]
