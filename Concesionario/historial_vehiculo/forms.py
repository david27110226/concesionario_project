from django import forms

from Concesionario.formularios import CampoFecha
from .models import Mantenimiento, Siniestro


class FormularioPropietario(forms.Form):
    nombre = forms.CharField(label='Nombre del propietario', max_length=100)
    fecha_inicio = CampoFecha(label='Desde')
    fecha_fin = CampoFecha(label='Hasta')

    def clean(self):
        datos = super().clean()
        inicio, fin = datos.get('fecha_inicio'), datos.get('fecha_fin')
        if inicio and fin and fin < inicio:
            self.add_error('fecha_fin', 'La fecha final no puede ser anterior a la inicial.')
        return datos


class FormularioMantenimiento(forms.Form):
    tipo = forms.ChoiceField(label='Tipo de mantenimiento', choices=Mantenimiento.TIPOS)
    fecha = CampoFecha(label='Fecha')
    costo = forms.FloatField(label='Costo (COP)', min_value=0, required=False)
    descripcion = forms.CharField(label='Descripción', required=False,
                                  widget=forms.Textarea(attrs={'rows': 3}))


class FormularioSiniestro(forms.Form):
    tipo = forms.ChoiceField(label='Tipo de siniestro', choices=Siniestro.TIPOS)
    fecha = CampoFecha(label='Fecha')
    costo_reparacion = forms.FloatField(label='Costo de reparación (COP)', min_value=0, required=False)
    descripcion = forms.CharField(label='Descripción', required=False,
                                  widget=forms.Textarea(attrs={'rows': 3}))
