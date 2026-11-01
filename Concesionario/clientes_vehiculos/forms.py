from django import forms

from .models import (COMBUSTIBLES, CONDICIONES, ESTADOS_VEHICULO, TIPOS_DOCUMENTO,
                     TIPOS_VEHICULO, TRANSMISIONES)


CAMPO_FECHA = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')


class FormularioCliente(forms.Form):
    tipo_documento = forms.ChoiceField(label='Tipo de documento', choices=TIPOS_DOCUMENTO)
    documento = forms.CharField(label='Número de documento', min_length=5, max_length=20)
    nombre = forms.CharField(label='Nombre', max_length=100)
    apellido = forms.CharField(label='Apellido', max_length=100)
    telefono = forms.CharField(label='Teléfono', max_length=20)
    email = forms.EmailField(label='Correo electrónico', required=False)
    fecha_nacimiento = forms.DateField(label='Fecha de nacimiento', required=False,
                                       widget=CAMPO_FECHA, input_formats=['%Y-%m-%d'])
    ciudad = forms.CharField(label='Ciudad', max_length=60, required=False)
    barrio = forms.CharField(label='Barrio', max_length=60, required=False)
    calle = forms.CharField(label='Dirección', max_length=120, required=False)

    def __init__(self, *args, editando=False, **kwargs):
        super().__init__(*args, **kwargs)
        if editando:
            # El documento identifica al cliente dentro de ventas y facturas
            self.fields['documento'].disabled = True

    def clean(self):
        datos = super().clean()
        if datos.get('calle') and not datos.get('ciudad'):
            self.add_error('ciudad', 'Indica la ciudad de la dirección.')
        return datos


class FormularioVehiculo(forms.Form):
    placa = forms.CharField(label='Placa', max_length=10)
    marca = forms.CharField(label='Marca', max_length=50)
    modelo = forms.CharField(label='Modelo', max_length=50)
    anio = forms.IntegerField(label='Año', min_value=1950, max_value=2030)
    color = forms.CharField(label='Color', max_length=30)
    tipo = forms.ChoiceField(label='Tipo', choices=TIPOS_VEHICULO)
    condicion = forms.ChoiceField(label='Condición', choices=CONDICIONES)
    estado = forms.ChoiceField(label='Estado', choices=ESTADOS_VEHICULO)
    precio = forms.FloatField(label='Precio (COP)', min_value=0)
    kilometraje = forms.IntegerField(label='Kilometraje', min_value=0, initial=0)
    imagen_url = forms.URLField(label='URL de la imagen', required=False,
                                help_text='Enlace a una foto del vehículo (opcional).')
    motor = forms.CharField(label='Motor', max_length=50)
    cilindraje = forms.IntegerField(label='Cilindraje (cc)', min_value=0)
    transmision = forms.ChoiceField(label='Transmisión', choices=TRANSMISIONES)
    combustible = forms.ChoiceField(label='Combustible', choices=COMBUSTIBLES)
    puertas = forms.IntegerField(label='Puertas', min_value=2, max_value=6, initial=4)
    descripcion = forms.CharField(label='Descripción', required=False,
                                  widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, editando=False, **kwargs):
        super().__init__(*args, **kwargs)
        if editando:
            # La placa identifica al vehículo dentro de historiales, ventas y facturas
            self.fields['placa'].disabled = True

    def clean_placa(self):
        return self.cleaned_data['placa'].upper().replace(' ', '')
