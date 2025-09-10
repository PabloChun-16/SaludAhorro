from django import forms
from apps.mantenimiento.models import Condiciones_Almacenamiento

class CondicionesAlmacenamientoForm(forms.ModelForm):
    """
    Formulario para el modelo de Condiciones de Almacenamiento.
    Se utiliza para crear y actualizar registros.
    """
    class Meta:
        # Define el modelo a partir del cual se creará el formulario
        model = Condiciones_Almacenamiento
        
        # Especifica los campos del modelo que se incluirán en el formulario
        fields = ["nombre_condicion"]
        
        # Define widgets para personalizar la apariencia de los campos
        widgets = {
            "nombre_condicion": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ingrese el nombre de la condición de almacenamiento",
                }
            ),
        }