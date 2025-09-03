# apps/mantenimiento/usuarios/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from .models import Usuario

class UsuarioForm(forms.ModelForm):
    # Campos virtuales, NO existen en la BD
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,           # requerido solo para crear (lo validamos abajo)
        label="Contraseña"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label="Confirmar contraseña"
    )

    class Meta:
        model = Usuario
        # No incluimos password_hash para no mostrarlo
        fields = ["nombre", "apellido", "correo_electronico", "id_rol", "password", "confirm_password"]

    def clean(self):
        data = super().clean()
        pwd = data.get("password")
        cpw = data.get("confirm_password")

        # En creación, la contraseña es obligatoria
        if self.instance.pk is None and not pwd:
            raise ValidationError("La contraseña es obligatoria para crear un usuario.")

        # Si el usuario llenó algo en password/confirm, deben coincidir
        if pwd or cpw:
            if pwd != cpw:
                raise ValidationError("Las contraseñas no coinciden.")

        return data

    def save(self, commit=True):
        user = super().save(commit=False)

        # Si el formulario trae una contraseña, la hasheamos
        pwd = self.cleaned_data.get("password")
        if pwd:
            user.password_hash = make_password(pwd)   # ← aquí se hace el hash

        if commit:
            user.save()
            self.save_m2m()
        return user
