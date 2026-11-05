from django import forms

from .models import Cliente, Vehiculo


class FormularioCliente(forms.Form):
    cedula = forms.CharField(label='Cédula', min_length=5, max_length=20)
    nombre = forms.CharField(label='Nombre', max_length=100)
    apellido = forms.CharField(label='Apellido', max_length=100)
    telefono = forms.CharField(label='Teléfono', max_length=20)
    email = forms.EmailField(label='Correo electrónico', required=False)
    direccion = forms.CharField(label='Dirección', required=False,
                                widget=forms.Textarea(attrs={'rows': 2}))

    def __init__(self, *args, editando=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.editando = editando
        if editando:
            # La cédula identifica al cliente: no se cambia
            self.fields['cedula'].disabled = True

    def clean_cedula(self):
        cedula = self.cleaned_data['cedula'].strip()
        if not cedula.isdigit():
            raise forms.ValidationError('La cédula solo puede tener números.')
        if not self.editando and Cliente.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError('Ya existe un cliente con esa cédula.')
        return cedula


class FormularioVehiculo(forms.Form):
    placa = forms.CharField(label='Placa', max_length=10)
    marca = forms.CharField(label='Marca', max_length=50)
    modelo = forms.CharField(label='Modelo', max_length=50)
    anio = forms.IntegerField(label='Año', min_value=1950, max_value=2030)
    color = forms.CharField(label='Color', max_length=30, required=False)
    precio = forms.FloatField(label='Precio (COP)', min_value=0)
    kilometraje = forms.IntegerField(label='Kilometraje', min_value=0, initial=0)
    estado = forms.ChoiceField(label='Estado', choices=Vehiculo.ESTADOS)
    descripcion = forms.CharField(label='Descripción', required=False,
                                  widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, editando=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.editando = editando
        if editando:
            # La placa es única y queda copiada en cotizaciones y facturas
            self.fields['placa'].disabled = True

    def clean_placa(self):
        placa = self.cleaned_data['placa'].strip().upper().replace(' ', '')
        if not self.editando and Vehiculo.objects.filter(placa=placa).exists():
            raise forms.ValidationError('Ya existe un vehículo con esa placa.')
        return placa
