from decimal import Decimal

from django import forms
from django.core.validators import URLValidator

from .models import Servicio, Tarifa

PRECIO_MAX = Decimal('99999999.99')


def _precio(etiqueta='Precio'):
    return forms.DecimalField(
        label=etiqueta, max_digits=10, decimal_places=2, localize=False,
        error_messages={
            'required': 'Escribe el precio.',
            'invalid': 'Escribe un precio válido, por ejemplo 12.50.',
            'max_digits': 'El precio es demasiado grande.',
            'max_decimal_places': 'Usa máximo 2 decimales.',
            'max_whole_digits': 'El precio es demasiado grande.',
        },
    )


def _precio_valido(valor):
    if valor is None:
        return valor
    if valor <= 0:
        raise forms.ValidationError('El precio debe ser mayor que 0.')
    return valor


class TarifaForm(forms.ModelForm):
    precio = _precio()

    class Meta:
        model = Tarifa
        fields = ['nombre', 'precio']

    def clean_nombre(self):
        nombre = ' '.join(self.cleaned_data['nombre'].split())
        if len(nombre) < 3:
            raise forms.ValidationError('El nombre es muy corto.')
        if Tarifa.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe una tarifa con ese nombre.')
        return nombre

    def clean_precio(self):
        return _precio_valido(self.cleaned_data.get('precio'))

    def validate_unique(self):
        pass  # ya se valida sin distinguir mayúsculas en clean_nombre


class ServicioForm(forms.ModelForm):
    precio_base = _precio('Precio base')
    imagen = forms.CharField(required=False, max_length=500)

    class Meta:
        model = Servicio
        fields = ['imagen', 'nombre', 'precio_base']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_imagen(self):
        url = self.cleaned_data.get('imagen', '').strip()
        if url:
            try:
                URLValidator(schemes=['http', 'https'])(url)
            except forms.ValidationError:
                raise forms.ValidationError('Escribe un vínculo válido que empiece por https://')
        return url

    def clean_nombre(self):
        nombre = ' '.join(self.cleaned_data['nombre'].split())
        if len(nombre) < 3:
            raise forms.ValidationError('El nombre es muy corto.')
        if Servicio.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe un servicio con ese nombre.')
        return nombre

    def clean_precio_base(self):
        return _precio_valido(self.cleaned_data.get('precio_base'))

    def validate_unique(self):
        pass


class PrecioForm(forms.Form):
    """Cambio rápido del precio de una tarifa o de un servicio."""

    precio = _precio()

    def clean_precio(self):
        return _precio_valido(self.cleaned_data.get('precio'))


class IvaForm(forms.Form):
    valor = forms.DecimalField(
        max_digits=5, decimal_places=2, localize=False, min_value=0, max_value=100,
        error_messages={
            'required': 'Escribe el porcentaje de IVA.',
            'invalid': 'Escribe un número, por ejemplo 15.',
            'min_value': 'El IVA debe estar entre 0 y 100.',
            'max_value': 'El IVA debe estar entre 0 y 100.',
            'max_decimal_places': 'Usa máximo 2 decimales.',
        },
    )
