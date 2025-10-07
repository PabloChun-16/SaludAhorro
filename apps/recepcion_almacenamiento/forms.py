# apps/recepcion_almacenamiento/forms.py
from django import forms
from django.utils import timezone
from datetime import datetime

from .models import Recepciones_Envio, Detalle_Recepcion
from apps.inventario.models import Lotes


class RecepcionForm(forms.ModelForm):
    """
    Form del encabezado de la recepción.
    - Acepta <input type="datetime-local"> para fecha_recepcion.
    - Requiere numero_envio_bodega (aunque en el modelo sea null/blank).
    - Devuelve la fecha como aware (en la TZ actual).
    """
    fecha_recepcion = forms.DateTimeField(
        input_formats=[
            "%Y-%m-%dT%H:%M",     # datetime-local del navegador
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
        ],
        required=True,
        error_messages={"invalid": "Formato de fecha/hora inválido."},
    )
    numero_envio_bodega = forms.CharField(
        required=True,
        error_messages={"required": "Debes ingresar el número de envío."},
    )

    class Meta:
        model = Recepciones_Envio
        fields = ["fecha_recepcion", "numero_envio_bodega"]
        widgets = {
            "fecha_recepcion": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "numero_envio_bodega": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej. ENVIOS-A-21463"}
            ),
        }
        labels = {
            "fecha_recepcion": "Fecha de Recepción",
            "numero_envio_bodega": "Número de Envío (Bodega)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si no viene fecha en data ni en initial, propón "ahora" (redondeado a minutos)
        data_has_fecha = hasattr(self, "data") and self.data.get("fecha_recepcion")
        if not data_has_fecha and not self.initial.get("fecha_recepcion"):
            now_local = timezone.localtime().replace(second=0, microsecond=0)
            # Para el widget datetime-local se espera 'YYYY-MM-DDTHH:MM'
            self.initial["fecha_recepcion"] = now_local.strftime("%Y-%m-%dT%H:%M")

        # Asegura strip al número de envío
        self.fields["numero_envio_bodega"].strip = True

    def clean_numero_envio_bodega(self):
        v = (self.cleaned_data.get("numero_envio_bodega") or "").strip()
        if not v:
            raise forms.ValidationError("Debes ingresar el número de envío.")
        return v

    def clean_fecha_recepcion(self):
        dt = self.cleaned_data["fecha_recepcion"]
        # Si llega naive, vuelve la fecha/hora aware en la TZ actual
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt


# ----------------------------------------------------------------------
# Opcional: solo si alguna vez usas formularios (no JSON) para el detalle
# ----------------------------------------------------------------------
class DetalleRecepcionForm(forms.ModelForm):
    """
    Este form NO se usa en el flujo actual (detalle via JSON).
    Lo dejamos por si necesitas una versión server-rendered del detalle.
    """
    # Campo auxiliar UI (no va a la DB)
    producto = forms.CharField(required=False)

    # Validaciones mínimas
    id_lote = forms.ModelChoiceField(queryset=Lotes.objects.all(), required=True)
    cantidad_recibida = forms.IntegerField(min_value=1, required=True)
    costo_unitario = forms.DecimalField(min_value=0, max_digits=10, decimal_places=2, required=False)

    class Meta:
        model = Detalle_Recepcion
        fields = ["id_lote", "cantidad_recibida", "costo_unitario"]

    def save(self, commit=True, recepcion=None):
        detalle = super().save(commit=False)
        if recepcion:
            detalle.id_recepcion = recepcion
        if detalle.costo_unitario is None:
            detalle.costo_unitario = 0
        if commit:
            detalle.save()
        return detalle
