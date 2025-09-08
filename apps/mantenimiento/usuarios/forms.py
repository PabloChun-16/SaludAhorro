from django import forms
from .models import Usuario

class UsuarioForm(forms.ModelForm):
    contrasena = forms.CharField(
        label="Contraseña",
        required=True,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "autocomplete": "new-password",
            "spellcheck": "false",
        })
    )
    confirmar_contrasena = forms.CharField(
        label="Confirmar contraseña",
        required=True,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "autocomplete": "new-password",
            "spellcheck": "false",
        })
    )

    class Meta:
        model = Usuario
        # 👇 SOLO campos del modelo
        fields = ["nombre", "apellido", "correo_electronico", "id_rol"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "autocomplete": "off", "spellcheck": "false", "autocapitalize": "words"}),
            "apellido": forms.TextInput(attrs={"class": "form-control", "autocomplete": "off", "spellcheck": "false", "autocapitalize": "words"}),
            "correo_electronico": forms.EmailInput(attrs={"class": "form-control", "inputmode": "email", "autocomplete": "off", "spellcheck": "false"}),
            "id_rol": forms.Select(attrs={"class": "form-select", "autocomplete": "off"}),
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("contrasena")
        p2 = cleaned.get("confirmar_contrasena")
        if p1 and p2 and p1 != p2:
            self.add_error("confirmar_contrasena", "Las contraseñas no coinciden.")
        return cleaned

    def save(self, commit=True):
        usuario: Usuario = super().save(commit=False)
        # Hashear siempre en create; en update solo si viene nueva
        pwd = self.cleaned_data.get("contrasena")
        if pwd:
            usuario.set_password(pwd)
        if commit:
            usuario.save()
        return usuario
