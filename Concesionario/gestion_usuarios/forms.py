from django import forms

from .models import Usuario


# Roles disponibles: se copian dentro del usuario como objeto embebido (Rol)
ROLES = {
    'administrador': {
        'nombre': 'Administrador',
        'descripcion': 'Acceso total al sistema',
        'perm_clientes': True,
        'perm_ventas': True,
        'perm_historial': True,
        'perm_pagos': True,
        'perm_usuarios': True,
    },
    'gerente': {
        'nombre': 'Gerente',
        'descripcion': 'Supervisa ventas, clientes y pagos',
        'perm_clientes': True,
        'perm_ventas': True,
        'perm_historial': True,
        'perm_pagos': True,
        'perm_usuarios': False,
    },
    'asesor': {
        'nombre': 'Asesor',
        'descripcion': 'Gestiona clientes y ventas',
        'perm_clientes': True,
        'perm_ventas': True,
        'perm_historial': True,
        'perm_pagos': False,
        'perm_usuarios': False,
    },
    'cajero': {
        'nombre': 'Cajero',
        'descripcion': 'Registra y consulta pagos',
        'perm_clientes': False,
        'perm_ventas': False,
        'perm_historial': False,
        'perm_pagos': True,
        'perm_usuarios': False,
    },
}

OPCIONES_ROL = [(clave, rol['nombre']) for clave, rol in ROLES.items()]

MESES = [(1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'), (5, 'Mayo'), (6, 'Junio'),
         (7, 'Julio'), (8, 'Agosto'), (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'),
         (12, 'Diciembre')]


def clave_rol(rol):
    """Devuelve la clave de ROLES que corresponde al rol embebido de un usuario."""
    for clave, datos in ROLES.items():
        if rol and rol['nombre'] == datos['nombre']:
            return clave
    return ''


class FormularioLogin(forms.Form):
    nombre_usuario = forms.CharField(label='Nombre de usuario', max_length=150)
    contrasena = forms.CharField(label='Contraseña', widget=forms.PasswordInput)


class FormularioUsuario(forms.Form):
    nombre_usuario = forms.CharField(label='Nombre de usuario', max_length=150)
    contrasena = forms.CharField(label='Contraseña', max_length=128, required=False,
                                 widget=forms.PasswordInput)
    nombre = forms.CharField(label='Nombre', max_length=100)
    apellido = forms.CharField(label='Apellido', max_length=100)
    email = forms.EmailField(label='Correo electrónico')
    telefono = forms.CharField(label='Teléfono', max_length=20, required=False)
    rol = forms.ChoiceField(label='Rol', choices=OPCIONES_ROL)

    def __init__(self, *args, usuario=None, **kwargs):
        # usuario: el que se está editando (None cuando es nuevo)
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        if usuario:
            self.fields['nombre_usuario'].disabled = True
            self.fields['contrasena'].help_text = 'Déjala vacía para conservar la actual.'

    def clean_nombre_usuario(self):
        nombre_usuario = self.cleaned_data['nombre_usuario'].strip()
        if self.usuario is None and Usuario.objects.filter(nombre_usuario=nombre_usuario).exists():
            raise forms.ValidationError('Ya existe un usuario con ese nombre.')
        return nombre_usuario

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        for otro in Usuario.objects.filter(email=email):
            if self.usuario is None or otro.id != self.usuario.id:
                raise forms.ValidationError('Ese correo ya está registrado.')
        return email

    def clean_contrasena(self):
        contrasena = self.cleaned_data['contrasena']
        if self.usuario is None and not contrasena:
            raise forms.ValidationError('La contraseña es obligatoria.')
        if contrasena and len(contrasena) < 6:
            raise forms.ValidationError('La contraseña debe tener al menos 6 caracteres.')
        return contrasena


class FormularioMeta(forms.Form):
    mes = forms.TypedChoiceField(label='Mes', choices=MESES, coerce=int)
    anio = forms.IntegerField(label='Año', min_value=2020, max_value=2100)
    meta_ventas = forms.IntegerField(label='Meta de ventas', min_value=1)


class FormularioNotificacion(forms.Form):
    destinatario = forms.ChoiceField(label='Para')
    asunto = forms.CharField(label='Asunto', max_length=200)
    mensaje = forms.CharField(label='Mensaje', widget=forms.Textarea(attrs={'rows': 4}))

    def __init__(self, *args, remitente='', **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['destinatario'].choices = [('', 'Selecciona un usuario')] + [
            (u.nombre_usuario, f'{u.nombre} {u.apellido} · {u.nombre_usuario}')
            for u in Usuario.objects.all().order_by('nombre')
            if u.nombre_usuario != remitente and u.esta_activo
        ]
