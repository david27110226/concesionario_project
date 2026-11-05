from django import forms

from .models import Mantenimiento


CAMPO_FECHA = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')


class FormularioPropietario(forms.Form):
    nombre = forms.CharField(label='Nombre del propietario', max_length=100)
    fecha_inicio = forms.DateField(label='Desde', widget=CAMPO_FECHA, input_formats=['%Y-%m-%d'])
    fecha_fin = forms.DateField(label='Hasta', widget=CAMPO_FECHA, input_formats=['%Y-%m-%d'])

    def clean(self):
        datos = super().clean()
        inicio, fin = datos.get('fecha_inicio'), datos.get('fecha_fin')
        if inicio and fin and fin < inicio:
            self.add_error('fecha_fin', 'La fecha final no puede ser anterior a la inicial.')
        return datos


class FormularioMantenimiento(forms.Form):
    tipo = forms.ChoiceField(label='Tipo de mantenimiento', choices=Mantenimiento.TIPOS)
    fecha = forms.DateField(label='Fecha', widget=CAMPO_FECHA, input_formats=['%Y-%m-%d'])
    costo = forms.FloatField(label='Costo (COP)', min_value=0, required=False)
    descripcion = forms.CharField(label='Descripción', required=False,
                                  widget=forms.Textarea(attrs={'rows': 3}))
