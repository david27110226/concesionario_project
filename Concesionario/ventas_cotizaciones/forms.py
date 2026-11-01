from django import forms

from clientes_vehiculos.models import Cliente, Vehiculo
from gestion_usuarios.models import Usuario
from .models import FORMAS_PAGO


CAMPO_FECHA = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')


def opciones_clientes():
    return [('', 'Selecciona un cliente')] + [
        (c.documento, f"{c.nombre} {c.apellido} · {c.documento}")
        for c in Cliente.objects.all().order_by('nombre')
    ]


def opciones_vehiculos(incluir_placa=''):
    """Vehículos que se pueden ofrecer (no vendidos). Se puede forzar una placa
    para que aparezca aunque ya esté reservada."""
    return [('', 'Selecciona un vehículo')] + [
        (v.placa, f"{v.marca} {v.modelo} {v.anio} · {v.placa} · ${v.precio:,.0f}".replace(',', '.'))
        for v in Vehiculo.objects.exclude(estado='vendido').order_by('marca')
    ] + [
        (v.placa, f"{v.marca} {v.modelo} {v.anio} · {v.placa}")
        for v in Vehiculo.objects.filter(placa=incluir_placa, estado='vendido')
    ]


def opciones_vendedores():
    return [('', 'Selecciona un asesor')] + [
        (u.nombre_usuario, f"{u.nombre} {u.apellido} · {u.get_cargo_display()}")
        for u in Usuario.objects.all().order_by('nombre') if u.activo
    ]


class FormularioCotizacion(forms.Form):
    cliente = forms.ChoiceField(label='Cliente')
    vehiculo = forms.ChoiceField(label='Vehículo')
    vendedor = forms.ChoiceField(label='Asesor')
    fecha = forms.DateField(label='Fecha', widget=CAMPO_FECHA, input_formats=['%Y-%m-%d'])
    descuento_porcentaje = forms.FloatField(label='Descuento (%)', min_value=0, max_value=30,
                                            initial=0, help_text='Máximo 30 %.')
    vigencia_dias = forms.IntegerField(label='Vigencia (días)', min_value=1, max_value=90, initial=15)
    notas = forms.CharField(label='Notas', required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, placa_actual='', **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].choices = opciones_clientes()
        self.fields['vehiculo'].choices = opciones_vehiculos(placa_actual)
        self.fields['vendedor'].choices = opciones_vendedores()


class FormularioVenta(forms.Form):
    cliente = forms.ChoiceField(label='Cliente')
    vehiculo = forms.ChoiceField(label='Vehículo')
    vendedor = forms.ChoiceField(label='Asesor')
    precio_final = forms.FloatField(label='Precio final (COP)', min_value=0, required=False,
                                    help_text='Si lo dejas vacío se usa el precio del vehículo.')
    forma_pago = forms.ChoiceField(label='Forma de pago', choices=FORMAS_PAGO)
    fecha_venta = forms.DateField(label='Fecha de venta', widget=CAMPO_FECHA, input_formats=['%Y-%m-%d'])
    observaciones = forms.CharField(label='Observaciones', required=False,
                                    widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].choices = opciones_clientes()
        self.fields['vehiculo'].choices = opciones_vehiculos()
        self.fields['vendedor'].choices = opciones_vendedores()


class FormularioEditarVenta(forms.Form):
    precio_final = forms.FloatField(label='Precio final (COP)', min_value=0)
    forma_pago = forms.ChoiceField(label='Forma de pago', choices=FORMAS_PAGO)
    fecha_venta = forms.DateField(label='Fecha de venta', widget=CAMPO_FECHA, input_formats=['%Y-%m-%d'])
    observaciones = forms.CharField(label='Observaciones', required=False,
                                    widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, facturada=False, **kwargs):
        super().__init__(*args, **kwargs)
        if facturada:
            # Una venta facturada no puede cambiar de precio
            self.fields['precio_final'].disabled = True
            self.fields['precio_final'].help_text = 'La venta ya fue facturada, el precio no se puede cambiar.'
