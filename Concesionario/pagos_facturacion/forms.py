from django import forms

from Concesionario.formularios import CampoFecha
from clientes_vehiculos.models import Cliente
from ventas_cotizaciones.models import Cotizacion
from .models import DetallePago


def opciones_ventas():
    """Ventas que todavía no tienen factura. El valor es el id de la cotización."""
    clientes = {c.id: c for c in Cliente.objects.all()}
    opciones = [('', 'Selecciona una venta')]
    for cotizacion in Cotizacion.objects.all().order_by('-id'):
        venta, vehiculo = cotizacion.venta, cotizacion.vehiculo
        cliente = clientes.get(cotizacion.id_cliente)
        if cliente and venta and not venta['numero_factura']:
            texto = (f'{cliente.nombre} {cliente.apellido} · {vehiculo["marca"]} '
                     f'{vehiculo["modelo"]} ({vehiculo["placa"]}) · '
                     f'${venta["precio_final"] or 0:,.0f}').replace(',', '.')
            opciones.append((str(cotizacion.id), texto))
    return opciones


class FormularioFactura(forms.Form):
    venta = forms.ChoiceField(label='Venta a facturar')
    iva_porcentaje = forms.FloatField(label='IVA (%)', min_value=0, max_value=50, initial=19)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['venta'].choices = opciones_ventas()


class FormularioEditarFactura(forms.Form):
    subtotal = forms.FloatField(label='Subtotal (COP)', min_value=1)
    iva_porcentaje = forms.FloatField(label='IVA (%)', min_value=0, max_value=50)

    def __init__(self, *args, pagado=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.pagado = pagado

    def clean(self):
        datos = super().clean()
        subtotal, iva = datos.get('subtotal'), datos.get('iva_porcentaje')
        if subtotal is not None and iva is not None and subtotal * (1 + iva / 100) < self.pagado:
            raise forms.ValidationError('El nuevo total no puede ser menor a lo que ya se ha pagado.')
        return datos


class FormularioPago(forms.Form):
    tipo_pago = forms.ChoiceField(label='Medio de pago', choices=DetallePago.TIPOS_PAGO)
    forma_pago = forms.ChoiceField(label='Forma', choices=DetallePago.FORMA_PAGO)
    monto = forms.FloatField(label='Monto (COP)', min_value=1)
    fecha_pago = CampoFecha(label='Fecha del pago')
    numero_referencia = forms.CharField(label='Número de referencia', max_length=50, required=False)
    observaciones = forms.CharField(label='Observaciones', required=False,
                                    widget=forms.Textarea(attrs={'rows': 2}))

    def __init__(self, *args, maximo=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.maximo = maximo
        self.fields['monto'].help_text = f'Saldo disponible: ${maximo:,.0f}'.replace(',', '.')

    def clean_monto(self):
        monto = self.cleaned_data['monto']
        if monto > self.maximo + 0.5:
            raise forms.ValidationError('El pago no puede superar el saldo pendiente.')
        return monto
