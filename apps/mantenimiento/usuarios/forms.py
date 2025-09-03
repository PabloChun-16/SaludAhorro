from django import forms
from .models import Usuario

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ["nombre", "apellido", "correo_electronico", "password_hash", "id_rol"]
        widgets = {
            "password_hash": forms.PasswordInput(),
        }
