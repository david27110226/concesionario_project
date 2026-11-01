from django.contrib.auth.hashers import make_password
from django.db.models import Q
from django.shortcuts import redirect, render

from ventas_cotizaciones.models import Cotizacion, Venta
from .forms import FormularioRol, FormularioUsuario
from .models import CARGOS, MODULOS, Rol, Usuario


def buscar_usuario(id):
    try:
        return Usuario.objects.get(id=id)
    except Usuario.DoesNotExist:
        return None


def buscar_rol(id):
    try:
        return Rol.objects.get(id=id)
    except Rol.DoesNotExist:
        return None


def rol_embebido(nombre_rol):
    """Devuelve el objeto que se guarda dentro del usuario a partir del nombre del rol."""
    if not nombre_rol:
        return None
    rol = Rol.objects.filter(nombre=nombre_rol).first()
    if rol is None:
        return None
    return {'nombre': rol.nombre, 'descripcion': rol.descripcion}


# ---------------- Usuarios ----------------

def lista_usuarios(request):
    usuarios = Usuario.objects.all().order_by('nombre')
    busqueda = request.GET.get('q', '').strip()
    cargo = request.GET.get('cargo', '')

    if busqueda:
        usuarios = usuarios.filter(
            Q(nombre__icontains=busqueda) | Q(apellido__icontains=busqueda) |
            Q(nombre_usuario__icontains=busqueda) | Q(email__icontains=busqueda)
        )
    if cargo:
        usuarios = usuarios.filter(cargo=cargo)

    datos = {
        'usuarios': usuarios,
        'busqueda': busqueda,
        'cargo': cargo,
        'cargos': CARGOS,
        'total': Usuario.objects.count(),
    }
    return render(request, 'gestion_usuarios/lista_usuarios.html', datos)


def crear_usuario(request):
    if request.method == 'POST':
        formulario = FormularioUsuario(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            if Usuario.objects.filter(nombre_usuario=datos['nombre_usuario']).exists():
                formulario.add_error('nombre_usuario', 'Ya existe un usuario con ese nombre.')
            else:
                usuario = Usuario.objects.create(
                    nombre_usuario=datos['nombre_usuario'],
                    contrasena=make_password(datos['contrasena']),
                    nombre=datos['nombre'],
                    apellido=datos['apellido'],
                    email=datos['email'],
                    telefono=datos['telefono'],
                    cargo=datos['cargo'],
                    activo=datos['activo'],
                    rol=rol_embebido(datos['rol']),
                )
                return redirect('usuarios:detalle_usuario', id=usuario.id)
    else:
        formulario = FormularioUsuario()

    return render(request, 'gestion_usuarios/formulario_usuario.html', {
        'formulario': formulario,
        'titulo': 'Nuevo usuario',
    })


def detalle_usuario(request, id):
    usuario = buscar_usuario(id)
    if usuario is None:
        return redirect('usuarios:lista_usuarios')

    # Ventas y cotizaciones donde el usuario aparece embebido como asesor
    ventas = Venta.objects.filter(vendedor={'nombre_usuario': usuario.nombre_usuario}).order_by('-id')
    cotizaciones = Cotizacion.objects.filter(vendedor={'nombre_usuario': usuario.nombre_usuario}).order_by('-id')
    total_vendido = sum(v.precio_final for v in ventas if v.estado == 'activa')

    return render(request, 'gestion_usuarios/detalle_usuario.html', {
        'usuario': usuario,
        'ventas': ventas[:5],
        'cotizaciones': cotizaciones[:5],
        'cantidad_ventas': ventas.count(),
        'cantidad_cotizaciones': cotizaciones.count(),
        'total_vendido': total_vendido,
    })


def editar_usuario(request, id):
    usuario = buscar_usuario(id)
    if usuario is None:
        return redirect('usuarios:lista_usuarios')

    if request.method == 'POST':
        formulario = FormularioUsuario(request.POST, editando=True,
                                       initial={'nombre_usuario': usuario.nombre_usuario})
        if formulario.is_valid():
            datos = formulario.cleaned_data
            usuario.nombre = datos['nombre']
            usuario.apellido = datos['apellido']
            usuario.email = datos['email']
            usuario.telefono = datos['telefono']
            usuario.cargo = datos['cargo']
            usuario.activo = datos['activo']
            usuario.rol = rol_embebido(datos['rol'])
            if datos['contrasena']:
                usuario.contrasena = make_password(datos['contrasena'])
            usuario.save()
            return redirect('usuarios:detalle_usuario', id=usuario.id)
    else:
        formulario = FormularioUsuario(editando=True, initial={
            'nombre_usuario': usuario.nombre_usuario,
            'nombre': usuario.nombre,
            'apellido': usuario.apellido,
            'email': usuario.email,
            'telefono': usuario.telefono,
            'cargo': usuario.cargo,
            'activo': usuario.activo,
            'rol': usuario.rol['nombre'] if usuario.rol else '',
        })

    return render(request, 'gestion_usuarios/formulario_usuario.html', {
        'formulario': formulario,
        'titulo': f'Editar usuario {usuario.nombre_usuario}',
        'usuario': usuario,
    })


def cambiar_estado_usuario(request, id):
    if request.method == 'POST':
        usuario = buscar_usuario(id)
        if usuario is not None:
            Usuario.objects.filter(id=id).update(activo=not usuario.activo)
    return redirect('usuarios:detalle_usuario', id=id)


def eliminar_usuario(request, id):
    usuario = buscar_usuario(id)
    if usuario is None:
        return redirect('usuarios:lista_usuarios')

    tiene_ventas = Venta.objects.filter(vendedor={'nombre_usuario': usuario.nombre_usuario}).exists()
    if request.method == 'POST' and not tiene_ventas:
        usuario.delete()
        return redirect('usuarios:lista_usuarios')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar usuario',
        'objeto': f'{usuario.nombre_completo()} ({usuario.nombre_usuario})',
        'bloqueado': tiene_ventas,
        'motivo': 'El usuario tiene ventas registradas. Puedes desactivarlo en lugar de eliminarlo.',
        'url_cancelar': 'usuarios:detalle_usuario',
        'id_cancelar': usuario.id,
    })


# ---------------- Roles ----------------

def lista_roles(request):
    roles = Rol.objects.all().order_by('nombre')
    usuarios = list(Usuario.objects.all())
    for rol in roles:
        rol.cantidad_usuarios = len([u for u in usuarios if u.rol and u.rol['nombre'] == rol.nombre])
    return render(request, 'gestion_usuarios/lista_roles.html', {'roles': roles})


def datos_rol(formulario):
    nombres = dict(MODULOS)
    datos = formulario.cleaned_data
    return {
        'nombre': datos['nombre'],
        'descripcion': datos['descripcion'],
        'permisos': [{'modulo': m, 'nivel': datos['nivel']} for m in datos['modulos'] if m in nombres],
    }


def crear_rol(request):
    if request.method == 'POST':
        formulario = FormularioRol(request.POST)
        if formulario.is_valid():
            datos = datos_rol(formulario)
            if Rol.objects.filter(nombre=datos['nombre']).exists():
                formulario.add_error('nombre', 'Ya existe un rol con ese nombre.')
            else:
                Rol.objects.create(**datos)
                return redirect('usuarios:lista_roles')
    else:
        formulario = FormularioRol()

    return render(request, 'gestion_usuarios/formulario_rol.html', {
        'formulario': formulario,
        'titulo': 'Nuevo rol',
    })


def editar_rol(request, id):
    rol = buscar_rol(id)
    if rol is None:
        return redirect('usuarios:lista_roles')

    if request.method == 'POST':
        formulario = FormularioRol(request.POST)
        if formulario.is_valid():
            datos = datos_rol(formulario)
            if Rol.objects.filter(nombre=datos['nombre']).exclude(id=rol.id).exists():
                formulario.add_error('nombre', 'Ya existe un rol con ese nombre.')
            else:
                nombre_anterior = rol.nombre
                rol.nombre = datos['nombre']
                rol.descripcion = datos['descripcion']
                rol.permisos = datos['permisos']
                rol.save()
                # Se actualiza la copia del rol que está embebida en cada usuario
                for usuario in Usuario.objects.filter(rol={'nombre': nombre_anterior}):
                    usuario.rol = {'nombre': rol.nombre, 'descripcion': rol.descripcion}
                    usuario.save()
                return redirect('usuarios:lista_roles')
    else:
        formulario = FormularioRol(initial={
            'nombre': rol.nombre,
            'descripcion': rol.descripcion,
            'modulos': [p['modulo'] for p in rol.permisos],
            'nivel': rol.permisos[0]['nivel'] if rol.permisos else 'lectura',
        })

    return render(request, 'gestion_usuarios/formulario_rol.html', {
        'formulario': formulario,
        'titulo': f'Editar rol {rol.nombre}',
    })


def eliminar_rol(request, id):
    rol = buscar_rol(id)
    if rol is None:
        return redirect('usuarios:lista_roles')

    if request.method == 'POST':
        for usuario in Usuario.objects.filter(rol={'nombre': rol.nombre}):
            usuario.rol = None
            usuario.save()
        rol.delete()
        return redirect('usuarios:lista_roles')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar rol',
        'objeto': rol.nombre,
        'advertencia': 'Los usuarios que tengan este rol quedarán sin rol asignado.',
        'url_cancelar': 'usuarios:lista_roles',
    })
