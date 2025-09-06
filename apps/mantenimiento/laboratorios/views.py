from django.views.generic import TemplateView, ListView
from apps.mantenimiento.models import Laboratorios

class IndexView(TemplateView):
    template_name = "mantenimiento/laboratorios/index.html"

class LaboratorioListView(ListView):
    model = Laboratorios
    template_name = "mantenimiento_laboratorios/lista.html"
    context_object_name = "items"
    paginate_by = 20
