from django.views.generic import TemplateView, ListView
from apps.mantenimiento.models import Unidades_Medida

class IndexView(TemplateView):
    template_name = "mantenimiento/unidades/index.html"

class UnidadMedidaListView(ListView):
    model = Unidades_Medida
    template_name = "mantenimiento_unidadesmedida/lista.html"
    context_object_name = "items"
    paginate_by = 20
