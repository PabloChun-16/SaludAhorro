from django import forms
from apps.mantenimiento.models import Unidades_Medida

class UnidadesMedidaForm(forms.ModelForm):
    class Meta:
        model = Unidades_Medida
        fields = ["nombre_unidad"]
        widgets = {
            "nombre_unidad": forms.TextInput(attrs={"class": "form-control"}),
        }

