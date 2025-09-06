from django.views.generic import TemplateView, ListView
# importa el modelo centralizado
from apps.mantenimiento.models import Condiciones_Almacenamiento  # <-- ajusta si tu clase se llama distinto

class IndexView(TemplateView):
    template_name = "mantenimiento/condiciones/index.html"

class CondicionAlmacenamientoListView(ListView):
    model = Condiciones_Almacenamiento
    template_name = "mantenimiento_condicionesalmacenamiento/lista.html"
    context_object_name = "items"
    paginate_by = 20
