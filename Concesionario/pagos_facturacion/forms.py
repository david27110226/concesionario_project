from django import forms

from ventas_cotizaciones.models import Venta
from .models import FORMAS_PAGO, TIPOS_PAGO


CAMPO_FECHA = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')


class FormularioFactura(forms.Form):
    venta = forms.ChoiceField(label='Venta a facturar')
    fecha_emision = forms.DateField(label='Fecha de emisión', widget=CAMPO_FECHA, input_formats=['%Y-%m-%d'])
    fecha_vencimiento = forms.DateField(label='Fecha de vencimiento', widget=CAMPO_FECHA,
                                        input_formats=['%Y-%m-%d'])
    iva_porcentaje = forms.FloatField(label='IVA (%)', min_value=0, max_value=50, initial=19)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ventas activas que todavía no tienen factura
        self.fields['venta'].choices = [('', 'Selecciona una venta')] + [
            (v.numero, f"{v.numero} · {v.cliente['nombre_completo']} · "
                       f"{v.vehiculo['marca']} {v.vehiculo['modelo']}")
            for v in Venta.objects.filter(estado='activa').order_by('-id') if not v.facturada
        ]

    def clean(self):
        datos = super().clean()
        emision, vencimiento = datos.get('fecha_emision'), datos.get('fecha_vencimiento')
        if emision and vencimiento and vencimiento < emision:
            self.add_error('fecha_vencimiento', 'El vencimiento no puede ser anterior a la emisión.')
        return datos


class FormularioEditarFactura(forms.Form):
    fecha_emision = forms.DateField(label='Fecha de emisión', widget=CAMPO_FECHA, input_formats=['%Y-%m-%d'])
    fecha_vencimiento = forms.DateField(label='Fecha de vencimiento', widget=CAMPO_FECHA,
                                        input_formats=['%Y-%m-%d'])
    iva_porcentaje = forms.FloatField(label='IVA (%)', min_value=0, max_value=50,
                                      help_text='Al cambiarlo se recalculan subtotal e impuesto; el total no cambia.')

    def clean(self):
        datos = super().clean()
        emision, vencimiento = datos.get('fecha_emision'), datos.get('fecha_vencimiento')
        if emision and vencimiento and vencimiento < emision:
            self.add_error('fecha_vencimiento', 'El vencimiento no puede ser anterior a la emisión.')
        return datos


class FormularioPago(forms.Form):
    monto = forms.FloatField(label='Monto (COP)', min_value=1)
    tipo_pago = forms.ChoiceField(label='Medio de pago', choices=TIPOS_PAGO)
    forma_pago = forms.ChoiceField(label='Forma', choices=FORMAS_PAGO)
    fecha_pago = forms.DateField(label='Fecha del pago', widget=CAMPO_FECHA, input_formats=['%Y-%m-%d'])
    numero_referencia = forms.CharField(label='Número de referencia', max_length=50, required=False)
    observaciones = forms.CharField(label='Observaciones', max_length=300, required=False,
                                    widget=forms.Textarea(attrs={'rows': 2}))

    def __init__(self, *args, saldo=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.saldo = saldo
        self.fields['monto'].help_text = f"Saldo pendiente: ${saldo:,.0f}".replace(',', '.')

    def clean_monto(self):
        monto = self.cleaned_data['monto']
        if monto > self.saldo + 0.5:
            raise forms.ValidationError('El pago no puede superar el saldo pendiente.')
        return monto
