from django import forms
from apps.inventario.models import Productos
from apps.mantenimiento.models import Estado_Producto  # para asignar "Activo"

class ProductoForm(forms.ModelForm):
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
            #id_estado_producto
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 2}),
            "imagen_url": forms.ClearableFileInput(attrs={"placeholder": "URL de la imagen"}),
        }

    def save(self, commit=True):
        obj = super().save(commit=False)
        # Si no viene seteado (creación), dejarlo en "Activo"
        if not obj.id_estado_producto_id:
            try:
                obj.id_estado_producto = Estado_Producto.objects.get(nombre_estado="Activo")
            except Estado_Producto.DoesNotExist:
                # Si tu modelo usa otro nombre de campo/valor, ajusta esto
                estado, _ = Estado_Producto.objects.get_or_create(nombre_estado="Activo")
                obj.id_estado_producto = estado
        if commit:
            obj.save()
            self.save_m2m()
        return obj
