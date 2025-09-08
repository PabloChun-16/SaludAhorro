from django import forms
from apps.mantenimiento.models import Laboratorio

class LaboratorioForm(forms.ModelForm):
    class Meta:
        model = Laboratorio
        fields = ["nombre_laboratorio"]
        widgets = {
            "nombre_laboratorio": forms.TextInput(attrs={"class": "form-control"}),
        }

