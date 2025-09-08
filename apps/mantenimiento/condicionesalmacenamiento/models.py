from django.views.generic import TemplateView, ListView
from apps.mantenimiento.models import Condiciones_Almacenamiento

class IndexView(TemplateView):
    template_name = "mantenimiento/condiciones/index.html"

class CondicionAlmacenamientoListView(ListView):
    model = Condiciones_Almacenamiento
    template_name = "mantenimiento/condiciones/lista.html"
    context_object_name = "items"
    paginate_by = 20

# Create your models here.
