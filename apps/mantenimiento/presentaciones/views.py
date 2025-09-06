from django.views.generic import TemplateView, ListView
from apps.mantenimiento.models import Presentaciones

class IndexView(TemplateView):
    template_name = "mantenimiento/presentaciones/index.html"

class PresentacionListView(ListView):
    model = Presentaciones
    template_name = "mantenimiento_presentaciones/lista.html"
    context_object_name = "items"
    paginate_by = 20
