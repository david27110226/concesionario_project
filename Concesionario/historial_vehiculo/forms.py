from django import forms

from clientes_vehiculos.models import Vehiculo
from .models import ESPECIALIDADES, TIPOS_MANTENIMIENTO, HistorialVehiculo, Taller


CAMPO_FECHA = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')


class FormularioHistorial(forms.Form):
    vehiculo = forms.ChoiceField(label='Vehículo')
    observaciones = forms.CharField(label='Observaciones', required=False,
                                    widget=forms.Textarea(attrs={'rows': 4}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo los vehículos que todavía no tienen historial
        con_historial = [h.vehiculo['placa'] for h in HistorialVehiculo.objects.all()]
        self.fields['vehiculo'].choices = [('', 'Selecciona un vehículo')] + [
            (v.placa, f"{v.placa} · {v.marca} {v.modelo} {v.anio}")
            for v in Vehiculo.objects.all().order_by('marca')
            if v.placa not in con_historial
        ]


class FormularioObservaciones(forms.Form):
    observaciones = forms.CharField(label='Observaciones', required=False,
                                    widget=forms.Textarea(attrs={'rows': 5}))


class FormularioMantenimiento(forms.Form):
    tipo = forms.ChoiceField(label='Tipo de mantenimiento', choices=TIPOS_MANTENIMIENTO)
    fecha = forms.DateField(label='Fecha', widget=CAMPO_FECHA, input_formats=['%Y-%m-%d'])
    kilometraje = forms.IntegerField(label='Kilometraje', min_value=0)
    costo = forms.FloatField(label='Costo (COP)', min_value=0)
    taller = forms.ChoiceField(label='Taller')
    descripcion = forms.CharField(label='Descripción', max_length=300, required=False,
                                  widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['taller'].choices = [('', 'Selecciona un taller')] + [
            (t.nombre, f"{t.nombre} · {t.ciudad}") for t in Taller.objects.all().order_by('nombre')
        ]


class FormularioPropietario(forms.Form):
    nombre = forms.CharField(label='Nombre del propietario', max_length=150)
    documento = forms.CharField(label='Documento', max_length=20, required=False)
    fecha_inicio = forms.DateField(label='Desde', widget=CAMPO_FECHA, input_formats=['%Y-%m-%d'])
    fecha_fin = forms.DateField(label='Hasta', widget=CAMPO_FECHA, input_formats=['%Y-%m-%d'])

    def clean(self):
        datos = super().clean()
        inicio, fin = datos.get('fecha_inicio'), datos.get('fecha_fin')
        if inicio and fin and fin < inicio:
            self.add_error('fecha_fin', 'La fecha final no puede ser anterior a la inicial.')
        return datos


class FormularioTaller(forms.Form):
    nombre = forms.CharField(label='Nombre del taller', max_length=100)
    nit = forms.CharField(label='NIT', max_length=20)
    telefono = forms.CharField(label='Teléfono', max_length=20)
    ciudad = forms.CharField(label='Ciudad', max_length=60)
    especialidad = forms.ChoiceField(label='Especialidad', choices=ESPECIALIDADES)
