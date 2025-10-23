from django.urls import path
from . import views

app_name = "devoluciones"

urlpatterns = [
    # 1) Lista principal
    path("", views.devolucion_list, name="list"),

    # 2) Crear (GET: partial del form / POST: guardar)
    path("crear/", views.devolucion_create, name="create"),

    # 3) Lotes vendidos en una factura para un producto concreto
    #    (usar en el modal de lotes del form)
    path(
        "lotes-por-factura/<str:ref>/<int:producto_id>/",
        views.lotes_vendidos_por_factura,
        name="lotes_por_factura",
    ),

    # CANCELAR (colocar antes del detail para que no lo capture)
    path("<str:ref>/cancelar/", views.devolucion_cancel, name="cancel"),

    # 5) Detalle de una devolución por No. de factura (dejar SIEMPRE al final)
    path("<str:ref>/", views.devolucion_detail, name="detail"),
]
