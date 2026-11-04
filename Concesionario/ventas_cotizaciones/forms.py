import datetime

from django import forms

from clientes_vehiculos.models import Cliente, Vehiculo
from gestion_usuarios.models import Usuario
from .models import (
    ESTADOS_ENTREGA, ESTADOS_GARANTIA, FORMAS_PAGO, MEDIOS_CONTACTO, RESULTADOS_SEGUIMIENTO,
    TIPOS_GARANTIA, Cotizacion, Promocion, Venta,
)


CAMPO_FECHA = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')
FORMATO_FECHA = ['%Y-%m-%d']


class SelectorCliente(forms.ModelChoiceField):
    def __init__(self, **kwargs):
        super().__init__(queryset=Cliente.objects.all().order_by('nombre'), label='Cliente',
                         empty_label='Selecciona un cliente', **kwargs)

    def label_from_instance(self, c):
        return f"{c.nombre} {c.apellido} · {c.documento}"


class SelectorVehiculo(forms.ModelChoiceField):

    def __init__(self, incluir=None, **kwargs):
        ids = [v.id for v in Vehiculo.objects.exclude(estado='vendido')]
        if incluir is not None and incluir not in ids:
            ids.append(incluir)
        super().__init__(queryset=Vehiculo.objects.filter(id__in=ids).order_by('marca'), label='Vehículo',
                         empty_label='Selecciona un vehiculo', **kwargs)

    def label_from_instance(self, v):
        return f"{v.marca} {v.modelo} {v.anio} · {v.placa} · ${v.precio:,.0f}".replace(',', '.')


class SelectorAsesor(forms.ModelChoiceField):
    def __init__(self, **kwargs):
        super().__init__(queryset=Usuario.objects.filter(activo=True).order_by('nombre'), label='Asesor',
                         empty_label='Selecciona un asesor', **kwargs)

    def label_from_instance(self, u):
        return f"{u.nombre} {u.apellido} · {u.get_cargo_display()}"


class SelectorPromocion(forms.ModelChoiceField):
    def __init__(self, incluir=None, **kwargs):
        ids = [p.id for p in Promocion.objects.filter(activa=True)
               if p.esta_vigente(datetime.date.today())]
        if incluir is not None and incluir not in ids:
            ids.append(incluir)
        super().__init__(queryset=Promocion.objects.filter(id__in=ids).order_by('nombre'), label='Promocion',
                         empty_label='Sin promocion', required=False,
                         help_text='Si eliges una promocion vigente, su porcentaje reemplaza al descuento manual.',
                         **kwargs)


class SelectorCotizacion(forms.ModelChoiceField):
    def __init__(self, incluir=None, **kwargs):
        ids = [c.id for c in Cotizacion.objects.exclude(estado__in=['vendida', 'rechazada'])]
        if incluir is not None and incluir not in ids:
            ids.append(incluir)
        super().__init__(queryset=Cotizacion.objects.filter(id__in=ids).order_by('-id'), label='Cotizacion',
                         empty_label='Selecciona una cotizacion', **kwargs)

    def label_from_instance(self, c):
        return f"{c.numero} · {c.cliente.nombre} {c.cliente.apellido} · {c.vehiculo.marca} {c.vehiculo.modelo}"


class SelectorVenta(forms.ModelChoiceField):
    def __init__(self, incluir=None, **kwargs):
        ids = [v.id for v in Venta.objects.filter(estado='activa')]
        if incluir is not None and incluir not in ids:
            ids.append(incluir)
        super().__init__(queryset=Venta.objects.filter(id__in=ids).order_by('-id'), label='Venta',
                         empty_label='Selecciona una venta', **kwargs)

    def label_from_instance(self, v):
        return f"{v.numero}  {v.cliente.nombre} {v.cliente.apellido} · {v.vehiculo.marca} {v.vehiculo.modelo}"


class FormularioCotizacion(forms.Form):
    fecha = forms.DateField(label='Fecha', widget=CAMPO_FECHA, input_formats=FORMATO_FECHA)
    descuento_porcentaje = forms.FloatField(label='Descuento (%)', min_value=0, max_value=30,
                                            initial=0, help_text='Maximo 30 %.')
    vigencia_dias = forms.IntegerField(label='Vigencia (dias)', min_value=1, max_value=90, initial=15)
    notas = forms.CharField(label='Notas', required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, vehiculo_actual=None, promocion_actual=None, **kwargs):
        super().__init__(*args, **kwargs)
        campos = {
            'cliente': SelectorCliente(),
            'vehiculo': SelectorVehiculo(incluir=vehiculo_actual),
            'vendedor': SelectorAsesor(),
            'promocion': SelectorPromocion(incluir=promocion_actual),
        }
        # Los selectores van primero, antes de la fecha y el descuento
        self.fields = {**campos, **self.fields}


class FormularioVenta(forms.Form):
    precio_final = forms.FloatField(label='Precio final (COP)', min_value=0, required=False,
                                    help_text='Si lo dejas vacio se usa el precio del vehiculo.')
    forma_pago = forms.ChoiceField(label='Forma de pago', choices=FORMAS_PAGO)
    fecha_venta = forms.DateField(label='Fecha de venta', widget=CAMPO_FECHA, input_formats=FORMATO_FECHA)
    observaciones = forms.CharField(label='Observaciones', required=False,
                                    widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        campos = {
            'cliente': SelectorCliente(),
            'vehiculo': SelectorVehiculo(),
            'vendedor': SelectorAsesor(),
        }
        self.fields = {**campos, **self.fields}


class FormularioEditarVenta(forms.Form):
    precio_final = forms.FloatField(label='Precio final (COP)', min_value=0)
    forma_pago = forms.ChoiceField(label='Forma de pago', choices=FORMAS_PAGO)
    fecha_venta = forms.DateField(label='Fecha de venta', widget=CAMPO_FECHA, input_formats=FORMATO_FECHA)
    observaciones = forms.CharField(label='Observaciones', required=False,
                                    widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, facturada=False, **kwargs):
        super().__init__(*args, **kwargs)
        if facturada:
            # Una venta facturada no puede cambiar de precio
            self.fields['precio_final'].disabled = True
            self.fields['precio_final'].help_text = 'La venta ya fue facturada, el precio no se puede cambiar.'


class FormularioPromocion(forms.Form):
    nombre = forms.CharField(label='Nombre', max_length=80)
    descripcion = forms.CharField(label='Descripcion', max_length=250, required=False)
    porcentaje = forms.FloatField(label='Descuento (%)', min_value=1, max_value=30,
                                  help_text='Entre 1 % y 30 %.')
    fecha_inicio = forms.DateField(label='Inicia', widget=CAMPO_FECHA, input_formats=FORMATO_FECHA)
    fecha_fin = forms.DateField(label='Termina', widget=CAMPO_FECHA, input_formats=FORMATO_FECHA)
    activa = forms.BooleanField(label='Promocion activa', required=False, initial=True)

    def clean(self):
        datos = super().clean()
        inicio, fin = datos.get('fecha_inicio'), datos.get('fecha_fin')
        if inicio and fin and fin < inicio:
            self.add_error('fecha_fin', 'La fecha final no puede ser anterior a la inicial.')
        return datos


class FormularioSeguimiento(forms.Form):
    fecha = forms.DateField(label='Fecha del contacto', widget=CAMPO_FECHA, input_formats=FORMATO_FECHA)
    medio = forms.ChoiceField(label='Medio', choices=MEDIOS_CONTACTO)
    resultado = forms.ChoiceField(label='Resultado', choices=RESULTADOS_SEGUIMIENTO)
    comentario = forms.CharField(label='Comentario', max_length=300,
                                 widget=forms.Textarea(attrs={'rows': 3}))
    proxima_fecha = forms.DateField(label='Proximo contacto', required=False, widget=CAMPO_FECHA,
                                    input_formats=FORMATO_FECHA)

    def __init__(self, *args, cotizacion_actual=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = {'cotizacion': SelectorCotizacion(incluir=cotizacion_actual), **self.fields}

    def clean(self):
        datos = super().clean()
        fecha, proxima = datos.get('fecha'), datos.get('proxima_fecha')
        if fecha and proxima and proxima < fecha:
            self.add_error('proxima_fecha', 'El proximo contacto no puede ser anterior al actual.')
        return datos


class FormularioEntrega(forms.Form):
    fecha_programada = forms.DateField(label='Fecha programada', widget=CAMPO_FECHA, input_formats=FORMATO_FECHA)
    lugar = forms.CharField(label='Lugar de entrega', max_length=120)
    estado = forms.ChoiceField(label='Estado', choices=ESTADOS_ENTREGA)
    fecha_entrega = forms.DateField(label='Fecha real de entrega', required=False, widget=CAMPO_FECHA,
                                    input_formats=FORMATO_FECHA,
                                    help_text='Obligatoria cuando el estado es Entregada.')
    observaciones = forms.CharField(label='Observaciones', max_length=300, required=False,
                                    widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, venta_actual=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = {'venta': SelectorVenta(incluir=venta_actual), **self.fields}

    def clean(self):
        datos = super().clean()
        if datos.get('estado') == 'entregada' and not datos.get('fecha_entrega'):
            self.add_error('fecha_entrega', 'Indica la fecha en que se entrego el vehiculo.')
        return datos


class FormularioGarantia(forms.Form):
    tipo = forms.ChoiceField(label='Tipo de garantia', choices=TIPOS_GARANTIA)
    meses = forms.IntegerField(label='Duracion (meses)', min_value=1, max_value=120, initial=12)
    kilometraje_limite = forms.IntegerField(label='Limite de kilometraje', min_value=1, initial=20000)
    fecha_inicio = forms.DateField(label='Fecha de inicio', widget=CAMPO_FECHA, input_formats=FORMATO_FECHA)
    estado = forms.ChoiceField(label='Estado', choices=ESTADOS_GARANTIA)
    cobertura = forms.CharField(label='Cobertura', max_length=300, required=False,
                                widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, venta_actual=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = {'venta': SelectorVenta(incluir=venta_actual), **self.fields}
