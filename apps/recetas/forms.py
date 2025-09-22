from django import forms
from apps.recetas.models import RecetaMedica, EnvioReceta, DetalleEnvioReceta, Producto, Usuario
from apps.inventario.models import Productos
from django.contrib.auth.models import User


# Formulario para registrar recetas médicas
class RecetaMedicaForm(forms.ModelForm):
    class Meta:
        model = RecetaMedica
        fields = ["referencia_factura", "referente_receta", "id_producto", "id_usuario_venta"]

        widgets = {
            "referencia_factura": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ingrese referencia de factura"
            }),
            "referente_receta": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ingrese referente de receta"
            }),
            "id_producto": forms.Select(attrs={
                "class": "form-control"
            }),
            "id_usuario_venta": forms.Select(attrs={
                "class": "form-control"
            }),
        }
class RecetaForm(forms.ModelForm):
    class Meta:
        model = RecetaMedica
        fields = ["referencia_factura", "referente_receta", "id_producto", "id_usuario_venta"]
        widgets = {
            "referencia_factura": forms.TextInput(attrs={"class": "form-control"}),
            "referente_receta": forms.TextInput(attrs={"class": "form-control"}),
            "id_producto": forms.Select(attrs={"class": "form-control"}),
            "id_usuario_venta": forms.Select(attrs={"class": "form-control"}),
        }

# Formulario para registrar envíos de recetas
class EnvioRecetaForm(forms.ModelForm):
    class Meta:
        model = EnvioReceta
        fields = ['nombre_reporte', 'id_estado_envio', 'id_usuario']
        widgets = {
            'nombre_reporte': forms.TextInput(attrs={'class': 'form-control'}),
            'id_estado_envio': forms.Select(attrs={'class': 'form-control'}),
            'id_usuario': forms.Select(attrs={'class': 'form-control'}),
        }


# Formulario para detalle de envío (opcional, se puede manejar en la vista)
class DetalleEnvioRecetaForm(forms.ModelForm):
    class Meta:
        model = DetalleEnvioReceta
        fields = ['id_envio', 'id_receta']
        widgets = {
            'id_envio': forms.Select(attrs={'class': 'form-control'}),
            'id_receta': forms.Select(attrs={'class': 'form-control'}),
        }