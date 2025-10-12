from django import forms
from django.utils import timezone
from apps.ajustes_inventario.models import Inventario_Fisico


class AjusteSalidaForm(forms.ModelForm):
    """
    Formulario para registrar el encabezado de una Salida por Ajuste.
    Basado en el modelo Inventario_Fisico.
    """
    class Meta:
        model = Inventario_Fisico
        fields = ["estado"]
        widgets = {
            "estado": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ejemplo: Completado, En proceso, Cancelado, etc."
            }),
        }
        labels = {"estado": "Estado del Ajuste"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Por defecto, el estado se inicializa como “Completado”
        if not self.initial.get("estado"):
            self.initial["estado"] = "Completado"
