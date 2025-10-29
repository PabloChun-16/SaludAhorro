from django import forms
from django.forms import DecimalField, NumberInput
from apps.inventario.models import Productos
from apps.mantenimiento.models import Estado_Producto


class ProductoForm(forms.ModelForm):
    BOOL_CHOICES_NON_NULL = [("1", "Si"), ("0", "No")]
    precio_compra = DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
        label="Precio de Compra",
    )
    precio_venta = DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
        label="Precio de Venta",
    )

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

        for name in ("id_laboratorio", "id_unidad_medida", "id_presentacion", "id_condicion_almacenamiento"):
            field = self.fields.get(name)
            if field:
                field.empty_label = None
                field.required = True

        for name in ("requiere_receta", "es_controlado"):
            original = self.fields[name]
            self.fields[name] = forms.TypedChoiceField(
                required=True,
                choices=self.BOOL_CHOICES_NON_NULL,
                coerce=lambda v: v in ("1", True),
                widget=forms.Select(attrs={"class": "form-select", "required": True}),
                label=original.label,
            )
            if self.instance and getattr(self.instance, name, None) is not None:
                self.initial[name] = "1" if getattr(self.instance, name) else "0"

        if self.instance and getattr(self.instance, "pk", None):
            lotes_qs = getattr(self.instance, "lotes_set", None)
            if lotes_qs:
                lote = lotes_qs.order_by("-id").first()
                if lote:
                    if lote.precio_compra is not None:
                        self.fields["precio_compra"].initial = lote.precio_compra
                    if lote.precio_venta is not None:
                        self.fields["precio_venta"].initial = lote.precio_venta

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.requiere_receta = self.cleaned_data.get("requiere_receta") in (True, "1", 1)
        obj.es_controlado = self.cleaned_data.get("es_controlado") in (True, "1", 1)

        if not getattr(obj, "id_estado_producto_id", None):
            estado, _ = Estado_Producto.objects.get_or_create(nombre_estado="Activo")
            obj.id_estado_producto = estado

        if commit:
            obj.save()
            self.save_m2m()

            precio_compra = self.cleaned_data.get("precio_compra")
            precio_venta = self.cleaned_data.get("precio_venta")
            update_data = {}
            if precio_compra is not None:
                update_data["precio_compra"] = precio_compra
            if precio_venta is not None:
                update_data["precio_venta"] = precio_venta

            if update_data:
                lotes_qs = getattr(obj, "lotes_set", None)
                if lotes_qs:
                    lotes_qs.update(**update_data)

            obj.precio_compra_form = precio_compra
            obj.precio_venta_form = precio_venta

        return obj
