from django import forms

from Concesionario.formularios import CampoFecha
from clientes_vehiculos.models import Cliente, Vehiculo
from .models import Cotizacion, PlantillaCotizacion

FORMAS_PAGO = [
    ('contado', 'Contado'),
    ('credito', 'Crédito'),
]


# ---------------- Plantillas ----------------

class FormularioPlantilla(forms.Form):
    nombre = forms.CharField(label='Nombre de la plantilla', max_length=100)
    descripcion = forms.CharField(label='Descripción', required=False,
                                  widget=forms.Textarea(attrs={'rows': 2}))
    notas_adicionales = forms.CharField(label='Notas adicionales', required=False,
                                        widget=forms.Textarea(attrs={'rows': 2}))
    activa = forms.BooleanField(label='Plantilla activa', required=False, initial=True)

    def __init__(self, *args, plantilla=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.plantilla = plantilla

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        for otra in PlantillaCotizacion.objects.filter(nombre=nombre):
            if self.plantilla is None or otra.id != self.plantilla.id:
                raise forms.ValidationError('Ya existe una plantilla con ese nombre.')
        return nombre


class FormularioCondicion(forms.Form):
    titulo = forms.CharField(label='Título', max_length=150)
    contenido = forms.CharField(label='Contenido', widget=forms.Textarea(attrs={'rows': 3}))
    orden = forms.IntegerField(label='Orden', min_value=1, initial=1)


class FormularioDescuento(forms.Form):
    nombre = forms.CharField(label='Nombre del descuento', max_length=100)
    porcentaje = forms.FloatField(label='Porcentaje (%)', min_value=0.5, max_value=50)
    descripcion = forms.CharField(label='Descripción', required=False,
                                  widget=forms.Textarea(attrs={'rows': 2}))


# ---------------- Cotizaciones y ventas ----------------

def opciones_descuento():
    """Descuentos de las plantillas activas. El valor es 'id_plantilla-posición'."""
    opciones = [('', 'Sin descuento')]
    for plantilla in PlantillaCotizacion.objects.all().order_by('nombre'):
        if plantilla.activa:
            for indice, descuento in enumerate(plantilla.descuentos):
                opciones.append((f'{plantilla.id}-{indice}',
                                 f'{plantilla.nombre} · {descuento["nombre"]} ({descuento["porcentaje"]:g} %)'))
    return opciones


class FormularioCotizacion(forms.Form):
    cliente = forms.ChoiceField(label='Cliente')
    vehiculo = forms.ChoiceField(label='Vehículo')
    descuento = forms.ChoiceField(label='Descuento de plantilla', required=False)
    precio_ofertado = forms.FloatField(label='Precio ofertado (COP)', min_value=0, required=False,
                                       help_text='Si lo dejas vacío se calcula con el precio del vehículo y el descuento.')
    fecha = CampoFecha(label='Fecha')
    notas = forms.CharField(label='Notas', required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].choices = [('', 'Selecciona un cliente')] + [
            (str(c.id), f'{c.nombre} {c.apellido} · C.C. {c.cedula}')
            for c in Cliente.objects.all().order_by('nombre')
        ]
        self.fields['vehiculo'].choices = [('', 'Selecciona un vehículo')] + [
            (v.placa, f'{v.marca} {v.modelo} {v.anio} · {v.placa} · ${v.precio or 0:,.0f}'.replace(',', '.'))
            for v in Vehiculo.objects.exclude(estado='vendido').order_by('marca')
        ]
        self.fields['descuento'].choices = opciones_descuento()


class FormularioEditarCotizacion(forms.Form):
    precio_ofertado = forms.FloatField(label='Precio ofertado (COP)', min_value=0)
    fecha = CampoFecha(label='Fecha')
    estado = forms.ChoiceField(label='Estado', choices=Cotizacion.ESTADOS)
    notas = forms.CharField(label='Notas', required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, vendida=False, **kwargs):
        super().__init__(*args, **kwargs)
        if vendida:
            # Una cotización con venta ya no cambia de estado ni de precio
            self.fields['estado'].disabled = True
            self.fields['precio_ofertado'].disabled = True


class FormularioVenta(forms.Form):
    fecha_venta = CampoFecha(label='Fecha de venta')
    precio_final = forms.FloatField(label='Precio final (COP)', min_value=0)
    forma_pago = forms.ChoiceField(label='Forma de pago', choices=FORMAS_PAGO)
