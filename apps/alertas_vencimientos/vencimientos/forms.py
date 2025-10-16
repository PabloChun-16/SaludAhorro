from django import forms
from django.utils import timezone
from apps.alertas_vencimientos.models import Reportes_Vencimiento

class ReporteVencimientoForm(forms.ModelForm):
    """
    Formulario para registrar el encabezado de un Reporte de Vencimiento.
    """
    class Meta:
        model = Reportes_Vencimiento
        fields = ["documento", "observaciones"]
        widgets = {
            "documento": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ejemplo: Devolución por productos vencidos"
            }),
            "observaciones": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Ejemplo: Envío a bodega de productos próximos a vencer..."
            }),
        }
        labels = {
            "documento": "Nombre del Reporte",
            "observaciones": "Observaciones",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial.setdefault("documento", f"Reporte Vencimiento - {timezone.now().strftime('%d/%m/%Y')}")
