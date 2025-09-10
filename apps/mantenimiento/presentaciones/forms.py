from django import forms
from apps.mantenimiento.models import Presentaciones

class PresentacionForm(forms.ModelForm):
    class Meta:
        model = Presentaciones
        fields = ["nombre_presentacion"]
        widgets = {
            "nombre_presentacion": forms.TextInput(attrs={"class": "form-control"}),
        }