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

    path("buscar-facturas/", views.buscar_facturas_completadas, name="buscar_facturas"),
    path("productos/<str:ref>/", views.productos_por_factura, name="productos_por_factura"),



    # CANCELAR (colocar antes del detail para que no lo capture)
    path("<str:ref>/cancelar/", views.devolucion_cancel, name="cancel"),
    # ✅ Exportar PDF
    path("<str:ref>/exportar/", views.devolucion_export_pdf, name="devolucion_export_pdf"),

    # 5) Detalle de una devolución por No. de factura (dejar SIEMPRE al final)
    path("<str:ref>/", views.devolucion_detail, name="detail"),
]
