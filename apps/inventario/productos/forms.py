from django import forms
from apps.inventario.models import Productos
from apps.mantenimiento.models import Estado_Producto

class ProductoForm(forms.ModelForm):
    # Sí/No sin placeholder
    BOOL_CHOICES_NON_NULL = [("1", "Sí"), ("0", "No")]

    class Meta:
        model = Productos
        fields = [
            "codigo_producto",
            "nombre",
            "descripcion",
            "imagen_url",
            "requiere_receta",
            "es_controlado",
            "stock_minimo",
            "id_laboratorio",
            "id_unidad_medida",
            "id_presentacion",
            "id_condicion_almacenamiento",
        ]
        widgets = {
            "codigo_producto": forms.TextInput(attrs={"class": "form-control"}),
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "imagen_url": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "stock_minimo": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "id_laboratorio": forms.Select(attrs={"class": "form-select", "required": True}),
            "id_unidad_medida": forms.Select(attrs={"class": "form-select", "required": True}),
            "id_presentacion": forms.Select(attrs={"class": "form-select", "required": True}),
            "id_condicion_almacenamiento": forms.Select(attrs={"class": "form-select", "required": True}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # FKs: sin empty_label => no aparece "— Selecciona —"
        for name in ("id_laboratorio", "id_unidad_medida", "id_presentacion", "id_condicion_almacenamiento"):
            f = self.fields.get(name)
            if f:
                f.empty_label = None  # quita placeholder
                f.required = True

        # Booleanos como select Sí/No sin opción vacía
        for name in ("requiere_receta", "es_controlado"):
            self.fields[name] = forms.TypedChoiceField(
                required=True,
                choices=self.BOOL_CHOICES_NON_NULL,
                coerce=lambda v: v in ("1", True),
                widget=forms.Select(attrs={"class": "form-select", "required": True}),
                label=self.fields[name].label,
            )
            # valor inicial si hay instancia
            if self.instance and getattr(self.instance, name, None) is not None:
                self.initial[name] = "1" if getattr(self.instance, name) else "0"

    def save(self, commit=True):
        obj = super().save(commit=False)
        # mapea strings a booleanos reales por si acaso
        obj.requiere_receta = (self.cleaned_data.get("requiere_receta") in (True, "1", 1))
        obj.es_controlado   = (self.cleaned_data.get("es_controlado")   in (True, "1", 1))

        # Default "Activo" si no viene seteado
        if not getattr(obj, "id_estado_producto_id", None):
            estado, _ = Estado_Producto.objects.get_or_create(nombre_estado="Activo")
            obj.id_estado_producto = estado
        if commit:
            obj.save()
            self.save_m2m()
        return obj
