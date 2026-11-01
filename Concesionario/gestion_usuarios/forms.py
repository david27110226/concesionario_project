from django import forms

from .models import CARGOS, MODULOS, NIVELES, Rol


class FormularioUsuario(forms.Form):
    nombre_usuario = forms.CharField(label='Nombre de usuario', max_length=150)
    contrasena = forms.CharField(label='Contraseña', max_length=128, required=False,
                                 widget=forms.PasswordInput(render_value=False),
                                 help_text='Mínimo 6 caracteres. Al editar, déjala vacía para conservar la actual.')
    nombre = forms.CharField(label='Nombre', max_length=100)
    apellido = forms.CharField(label='Apellido', max_length=100)
    email = forms.EmailField(label='Correo electrónico')
    telefono = forms.CharField(label='Teléfono', max_length=20, required=False)
    cargo = forms.ChoiceField(label='Cargo', choices=CARGOS)
    rol = forms.ChoiceField(label='Rol', required=False)
    activo = forms.BooleanField(label='Usuario activo', required=False, initial=True)

    def __init__(self, *args, editando=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.editando = editando
        self.fields['rol'].choices = [('', 'Sin rol')] + [
            (r.nombre, r.nombre) for r in Rol.objects.all().order_by('nombre')
        ]
        if editando:
            # El nombre de usuario identifica al vendedor dentro de cotizaciones y ventas
            self.fields['nombre_usuario'].disabled = True

    def clean_contrasena(self):
        contrasena = self.cleaned_data['contrasena']
        if not self.editando and not contrasena:
            raise forms.ValidationError('La contraseña es obligatoria.')
        if contrasena and len(contrasena) < 6:
            raise forms.ValidationError('La contraseña debe tener al menos 6 caracteres.')
        return contrasena


class FormularioRol(forms.Form):
    nombre = forms.CharField(label='Nombre del rol', max_length=50)
    descripcion = forms.CharField(label='Descripción', max_length=200, required=False,
                                  widget=forms.Textarea(attrs={'rows': 3}))
    modulos = forms.MultipleChoiceField(label='Módulos permitidos', choices=MODULOS,
                                        widget=forms.CheckboxSelectMultiple)
    nivel = forms.ChoiceField(label='Nivel de acceso', choices=NIVELES)
