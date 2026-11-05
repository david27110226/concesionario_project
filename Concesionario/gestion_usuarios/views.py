import datetime

from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Q
from django.shortcuts import redirect, render

from clientes_vehiculos.models import Cliente
from .forms import (MESES, ROLES, FormularioLogin, FormularioMeta, FormularioNotificacion,
                    FormularioUsuario, clave_rol)
from .models import Usuario
from .sesion import iniciar_sesion, registrar_auditoria, requiere_permiso


def buscar_usuario(id):
    try:
        return Usuario.objects.get(id=id)
    except Usuario.DoesNotExist:
        return None


def actualizar_metas(nombre_usuario):
    """Recalcula ventas_realizadas de cada meta del asesor a partir de las ventas registradas."""
    usuario = Usuario.objects.filter(nombre_usuario=nombre_usuario).first()
    if usuario is None or not usuario.metas:
        return
    fechas = []
    for cliente in Cliente.objects.all():
        for cotizacion in cliente.cotizaciones:
            venta = cotizacion['venta']
            if venta and cotizacion['vendedor']['nombre_usuario'] == nombre_usuario:
                fechas.append(venta['fecha_venta'])
    for meta in usuario.metas:
        meta['ventas_realizadas'] = len([f for f in fechas if f.month == meta['mes'] and f.year == meta['anio']])
    usuario.save()


def nombre_mes(numero):
    return dict(MESES)[numero]


# ---------------- Inicio y cierre de sesión ----------------

def login(request):
    if request.session.get('usuario'):
        return redirect('inicio')

    error = ''
    if request.method == 'POST':
        formulario = FormularioLogin(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            usuario = Usuario.objects.filter(nombre_usuario=datos['nombre_usuario']).first()
            if usuario is None or not check_password(datos['contrasena'], usuario.contrasena):
                if usuario:
                    registrar_auditoria(request, 'login', 'autenticación', 'Contraseña incorrecta',
                                        exitoso=False, usuario=usuario)
                error = 'Usuario o contraseña incorrectos.'
            elif not usuario.esta_activo:
                error = 'Tu usuario está deshabilitado. Comunícate con un administrador.'
            else:
                iniciar_sesion(request, usuario)
                registrar_auditoria(request, 'login', 'autenticación', 'Inicio de sesión exitoso', usuario=usuario)
                return redirect('inicio')
    else:
        formulario = FormularioLogin()

    return render(request, 'gestion_usuarios/login.html', {'formulario': formulario, 'error': error})


def registro(request):
    if request.method == 'POST':
        formulario = FormularioUsuario(request.POST)
        if formulario.is_valid():
            usuario = crear_desde_formulario(formulario.cleaned_data)
            iniciar_sesion(request, usuario)
            registrar_auditoria(request, 'crear', 'usuarios', 'Se registró en el sistema', usuario=usuario)
            return redirect('inicio')
    else:
        formulario = FormularioUsuario()

    return render(request, 'gestion_usuarios/registro.html', {'formulario': formulario})


def logout(request):
    if request.session.get('usuario'):
        registrar_auditoria(request, 'logout', 'autenticación', 'Cierre de sesión')
    request.session.flush()
    return redirect('usuarios:login')


def crear_desde_formulario(datos):
    rol = ROLES[datos['rol']]
    return Usuario.objects.create(
        nombre_usuario=datos['nombre_usuario'],
        contrasena=make_password(datos['contrasena']),
        nombre=datos['nombre'],
        apellido=datos['apellido'],
        email=datos['email'],
        telefono=datos['telefono'],
        es_administrador=datos['rol'] == 'administrador',
        es_superusuario=False,
        esta_activo=True,
        activo=True,
        rol=rol,
        auditoria=[],
        metas=[],
        notificaciones=[],
    )


# ---------------- CRUD de usuarios ----------------

@requiere_permiso('usuarios')
def lista_usuarios(request):
    usuarios = Usuario.objects.all().order_by('nombre')
    busqueda = request.GET.get('q', '').strip()
    rol = request.GET.get('rol', '')
    if busqueda:
        usuarios = usuarios.filter(
            Q(nombre__icontains=busqueda) | Q(apellido__icontains=busqueda) |
            Q(nombre_usuario__icontains=busqueda) | Q(email__icontains=busqueda)
        )
    if rol in ROLES:
        usuarios = [u for u in usuarios if clave_rol(u.rol) == rol]

    return render(request, 'gestion_usuarios/lista_usuarios.html', {
        'usuarios': usuarios,
        'busqueda': busqueda,
        'rol': rol,
        'roles': ROLES,
        'total': Usuario.objects.count(),
    })


@requiere_permiso('usuarios')
def crear_usuario(request):
    if request.method == 'POST':
        formulario = FormularioUsuario(request.POST)
        if formulario.is_valid():
            usuario = crear_desde_formulario(formulario.cleaned_data)
            registrar_auditoria(request, 'crear', 'usuarios', f'Creó el usuario {usuario.nombre_usuario}')
            return redirect('usuarios:detalle_usuario', id=usuario.id)
    else:
        formulario = FormularioUsuario()

    return render(request, 'gestion_usuarios/formulario_usuario.html', {
        'formulario': formulario,
        'titulo': 'Nuevo usuario',
    })


@requiere_permiso('usuarios')
def detalle_usuario(request, id):
    usuario = buscar_usuario(id)
    if usuario is None:
        return redirect('usuarios:lista_usuarios')

    metas = []
    for indice, meta in enumerate(usuario.metas):
        porcentaje = round(meta['ventas_realizadas'] * 100 / meta['meta_ventas'])
        metas.append(dict(meta, indice=indice, nombre_mes=nombre_mes(meta['mes']),
                          porcentaje=min(porcentaje, 100)))

    return render(request, 'gestion_usuarios/detalle_usuario.html', {
        'usuario': usuario,
        'metas': metas,
        'auditoria': list(reversed(usuario.auditoria))[:15],
        'permisos': [(m, usuario.rol and usuario.rol['perm_' + m]) for m in
                     ['clientes', 'historial', 'ventas', 'pagos', 'usuarios']],
    })


@requiere_permiso('usuarios')
def editar_usuario(request, id):
    usuario = buscar_usuario(id)
    if usuario is None:
        return redirect('usuarios:lista_usuarios')

    if request.method == 'POST':
        formulario = FormularioUsuario(request.POST, usuario=usuario,
                                       initial={'nombre_usuario': usuario.nombre_usuario})
        if formulario.is_valid():
            datos = formulario.cleaned_data
            usuario.nombre = datos['nombre']
            usuario.apellido = datos['apellido']
            usuario.email = datos['email']
            usuario.telefono = datos['telefono']
            usuario.rol = ROLES[datos['rol']]
            usuario.es_administrador = datos['rol'] == 'administrador'
            if datos['contrasena']:
                usuario.contrasena = make_password(datos['contrasena'])
            usuario.save()
            registrar_auditoria(request, 'editar', 'usuarios', f'Editó el usuario {usuario.nombre_usuario}')
            if usuario.id == request.session['usuario']['id']:
                iniciar_sesion(request, usuario)
            return redirect('usuarios:detalle_usuario', id=usuario.id)
    else:
        formulario = FormularioUsuario(usuario=usuario, initial={
            'nombre_usuario': usuario.nombre_usuario,
            'nombre': usuario.nombre,
            'apellido': usuario.apellido,
            'email': usuario.email,
            'telefono': usuario.telefono,
            'rol': clave_rol(usuario.rol),
        })

    return render(request, 'gestion_usuarios/formulario_usuario.html', {
        'formulario': formulario,
        'titulo': f'Editar usuario {usuario.nombre_usuario}',
        'usuario': usuario,
    })


@requiere_permiso('usuarios')
def cambiar_estado_usuario(request, id):
    usuario = buscar_usuario(id)
    if usuario and request.method == 'POST' and usuario.id != request.session['usuario']['id']:
        usuario.esta_activo = not usuario.esta_activo
        usuario.activo = usuario.esta_activo
        usuario.save()
        accion = 'Habilitó' if usuario.esta_activo else 'Deshabilitó'
        registrar_auditoria(request, 'editar', 'usuarios', f'{accion} al usuario {usuario.nombre_usuario}')
    return redirect('usuarios:detalle_usuario', id=id)


@requiere_permiso('usuarios')
def eliminar_usuario(request, id):
    usuario = buscar_usuario(id)
    if usuario is None:
        return redirect('usuarios:lista_usuarios')

    propio = usuario.id == request.session['usuario']['id']
    if request.method == 'POST' and not propio:
        usuario.delete()
        registrar_auditoria(request, 'eliminar', 'usuarios', f'Eliminó el usuario {usuario.nombre_usuario}')
        return redirect('usuarios:lista_usuarios')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar usuario',
        'objeto': f'{usuario.nombre} {usuario.apellido} ({usuario.nombre_usuario})',
        'bloqueado': propio,
        'motivo': 'No puedes eliminar el usuario con el que iniciaste sesión.',
        'url_cancelar': 'usuarios:detalle_usuario',
        'id_cancelar': usuario.id,
    })


# ---------------- Metas de ventas (embebidas en el usuario) ----------------

@requiere_permiso('usuarios')
def agregar_meta(request, id):
    usuario = buscar_usuario(id)
    if usuario is None:
        return redirect('usuarios:lista_usuarios')

    if request.method == 'POST':
        formulario = FormularioMeta(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            repetida = [m for m in usuario.metas if m['mes'] == datos['mes'] and m['anio'] == datos['anio']]
            if repetida:
                formulario.add_error('mes', 'El usuario ya tiene una meta para ese mes.')
            else:
                usuario.metas.append({
                    'mes': datos['mes'],
                    'anio': datos['anio'],
                    'meta_ventas': datos['meta_ventas'],
                    'ventas_realizadas': 0,
                    'fecha_asignacion': datetime.date.today(),
                })
                usuario.save()
                actualizar_metas(usuario.nombre_usuario)
                registrar_auditoria(request, 'crear', 'usuarios',
                                    f'Asignó meta de {nombre_mes(datos["mes"])} {datos["anio"]} a {usuario.nombre_usuario}')
                return redirect('usuarios:detalle_usuario', id=usuario.id)
    else:
        hoy = datetime.date.today()
        formulario = FormularioMeta(initial={'mes': hoy.month, 'anio': hoy.year})

    return render(request, 'gestion_usuarios/formulario_meta.html', {
        'formulario': formulario,
        'usuario': usuario,
    })


@requiere_permiso('usuarios')
def eliminar_meta(request, id, indice):
    usuario = buscar_usuario(id)
    if usuario and request.method == 'POST' and indice < len(usuario.metas):
        meta = usuario.metas.pop(indice)
        usuario.save()
        registrar_auditoria(request, 'eliminar', 'usuarios',
                            f'Eliminó la meta de {nombre_mes(meta["mes"])} {meta["anio"]} de {usuario.nombre_usuario}')
    return redirect('usuarios:detalle_usuario', id=id)


# ---------------- Notificaciones (embebidas en el usuario) ----------------

@requiere_permiso()
def notificaciones(request):
    usuario = buscar_usuario(request.session['usuario']['id'])
    lista = [dict(n, indice=i) for i, n in enumerate(usuario.notificaciones)]
    lista.reverse()
    return render(request, 'gestion_usuarios/notificaciones.html', {
        'notificaciones': lista,
        'no_leidas': len([n for n in lista if not n['leida']]),
    })


@requiere_permiso()
def enviar_notificacion(request):
    remitente = request.session['usuario']['nombre_usuario']
    if request.method == 'POST':
        formulario = FormularioNotificacion(request.POST, remitente=remitente)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            destinatario = Usuario.objects.get(nombre_usuario=datos['destinatario'])
            destinatario.notificaciones.append({
                'remitente': remitente,
                'asunto': datos['asunto'],
                'mensaje': datos['mensaje'],
                'fecha': datetime.datetime.now(),
                'leida': False,
                'fecha_lectura': None,
            })
            destinatario.save()
            registrar_auditoria(request, 'crear', 'notificaciones',
                                f'Envió la notificación "{datos["asunto"]}" a {destinatario.nombre_usuario}')
            return redirect('usuarios:notificaciones')
    else:
        formulario = FormularioNotificacion(remitente=remitente)

    return render(request, 'gestion_usuarios/formulario_notificacion.html', {'formulario': formulario})


@requiere_permiso()
def leer_notificacion(request, indice):
    usuario = buscar_usuario(request.session['usuario']['id'])
    if request.method == 'POST' and indice < len(usuario.notificaciones):
        notificacion = usuario.notificaciones[indice]
        if not notificacion['leida']:
            notificacion['leida'] = True
            notificacion['fecha_lectura'] = datetime.datetime.now()
            usuario.save()
    return redirect('usuarios:notificaciones')


@requiere_permiso()
def eliminar_notificacion(request, indice):
    usuario = buscar_usuario(request.session['usuario']['id'])
    if request.method == 'POST' and indice < len(usuario.notificaciones):
        usuario.notificaciones.pop(indice)
        usuario.save()
    return redirect('usuarios:notificaciones')
