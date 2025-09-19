# apps/recepcion_almacenamiento/forms.py
from django import forms
from .models import Recepciones_Envio, Detalle_Recepcion

class RecepcionForm(forms.ModelForm):
    class Meta:
        model = Recepciones_Envio
        fields = ["numero_envio_bodega", "fecha_recepcion", "estado_recepcion"]
        widgets = {
            "fecha_recepcion": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "numero_envio_bodega": forms.TextInput(attrs={"placeholder": "ENVIOS-A-21463"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha_recepcion"].input_formats = ["%Y-%m-%dT%H:%M"]


class DetalleRecepcionForm(forms.ModelForm):
    class Meta:
        model = Detalle_Recepcion
        fields = ["id_lote", "cantidad_recibida", "costo_unitario"]
