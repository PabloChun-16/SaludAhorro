from django.views.generic import TemplateView, ListView
from apps.mantenimiento.models import Roles  # <-- AJUSTA si tu clase se llama distinto

class IndexView(TemplateView):
    template_name = "mantenimiento/roles/index.html"

class RolListView(ListView):
    model = Roles
    template_name = "mantenimiento_roles/lista.html"
    context_object_name = "items"
    paginate_by = 20
