from django.db.models import Q
from django.shortcuts import redirect, render

from clientes_vehiculos.models import Vehiculo
from gestion_usuarios.sesion import registrar_auditoria, requiere_permiso
from .forms import FormularioMantenimiento, FormularioPropietario
from .models import Mantenimiento


def buscar_vehiculo(id):
    try:
        return Vehiculo.objects.get(id=id)
    except Vehiculo.DoesNotExist:
        return None


def nombre_tipo(tipo):
    return dict(Mantenimiento.TIPOS)[tipo]


@requiere_permiso('historial')
def lista_historiales(request):
    vehiculos = Vehiculo.objects.all().order_by('-anio')
    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        vehiculos = vehiculos.filter(
            Q(placa__icontains=busqueda) | Q(marca__icontains=busqueda) | Q(modelo__icontains=busqueda)
        )

    filas = []
    for vehiculo in vehiculos:
        fechas = [m['fecha'] for m in vehiculo.mantenimientos]
        filas.append({
            'vehiculo': vehiculo,
            'duenos': len(vehiculo.propietarios_anteriores),
            'mantenimientos': len(vehiculo.mantenimientos),
            'costo': sum(m['costo'] or 0 for m in vehiculo.mantenimientos),
            'ultimo': max(fechas) if fechas else None,
        })

    return render(request, 'historial_vehiculo/lista_historiales.html', {
        'filas': filas,
        'busqueda': busqueda,
        'total': Vehiculo.objects.count(),
    })


@requiere_permiso('historial')
def detalle_historial(request, id):
    vehiculo = buscar_vehiculo(id)
    if vehiculo is None:
        return redirect('historial:lista_historiales')

    mantenimientos = [dict(m, indice=i, nombre_tipo=nombre_tipo(m['tipo']))
                      for i, m in enumerate(vehiculo.mantenimientos)]
    mantenimientos.sort(key=lambda m: m['fecha'], reverse=True)
    propietarios = [dict(p, indice=i) for i, p in enumerate(vehiculo.propietarios_anteriores)]
    propietarios.sort(key=lambda p: p['fecha_inicio'])

    return render(request, 'historial_vehiculo/detalle_historial.html', {
        'vehiculo': vehiculo,
        'mantenimientos': mantenimientos,
        'propietarios': propietarios,
        'costo_total': sum(m['costo'] or 0 for m in mantenimientos),
    })


# ---------------- Propietarios anteriores ----------------

def propietario_repetido(vehiculo, datos, omitir=None):
    for i, dueno in enumerate(vehiculo.propietarios_anteriores):
        if i != omitir and dueno['nombre'].lower() == datos['nombre'].lower() \
                and dueno['fecha_inicio'] == datos['fecha_inicio']:
            return True
    return False


@requiere_permiso('historial')
def agregar_propietario(request, id):
    vehiculo = buscar_vehiculo(id)
    if vehiculo is None:
        return redirect('historial:lista_historiales')

    if request.method == 'POST':
        formulario = FormularioPropietario(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            if propietario_repetido(vehiculo, datos):
                formulario.add_error('nombre', 'Ese propietario ya está registrado con la misma fecha.')
            else:
                vehiculo.propietarios_anteriores.append({
                    'nombre': datos['nombre'],
                    'fecha_inicio': datos['fecha_inicio'],
                    'fecha_fin': datos['fecha_fin'],
                })
                vehiculo.save()
                registrar_auditoria(request, 'crear', 'historial',
                                    f'Registró a {datos["nombre"]} como dueño anterior de {vehiculo.placa}')
                return redirect('historial:detalle_historial', id=vehiculo.id)
    else:
        formulario = FormularioPropietario()

    return render(request, 'historial_vehiculo/formulario_registro.html', {
        'formulario': formulario,
        'vehiculo': vehiculo,
        'titulo': 'Registrar propietario anterior',
    })


@requiere_permiso('historial')
def editar_propietario(request, id, indice):
    vehiculo = buscar_vehiculo(id)
    if vehiculo is None or indice >= len(vehiculo.propietarios_anteriores):
        return redirect('historial:lista_historiales')

    dueno = vehiculo.propietarios_anteriores[indice]
    if request.method == 'POST':
        formulario = FormularioPropietario(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            if propietario_repetido(vehiculo, datos, omitir=indice):
                formulario.add_error('nombre', 'Ese propietario ya está registrado con la misma fecha.')
            else:
                dueno['nombre'] = datos['nombre']
                dueno['fecha_inicio'] = datos['fecha_inicio']
                dueno['fecha_fin'] = datos['fecha_fin']
                vehiculo.save()
                registrar_auditoria(request, 'editar', 'historial',
                                    f'Modificó al dueño anterior {datos["nombre"]} de {vehiculo.placa}')
                return redirect('historial:detalle_historial', id=vehiculo.id)
    else:
        formulario = FormularioPropietario(initial=dueno)

    return render(request, 'historial_vehiculo/formulario_registro.html', {
        'formulario': formulario,
        'vehiculo': vehiculo,
        'titulo': 'Modificar propietario anterior',
    })


@requiere_permiso('historial')
def eliminar_propietario(request, id, indice):
    vehiculo = buscar_vehiculo(id)
    if vehiculo is None or indice >= len(vehiculo.propietarios_anteriores):
        return redirect('historial:lista_historiales')

    dueno = vehiculo.propietarios_anteriores[indice]
    if request.method == 'POST':
        vehiculo.propietarios_anteriores.pop(indice)
        vehiculo.save()
        registrar_auditoria(request, 'eliminar', 'historial',
                            f'Borró a {dueno["nombre"]} del historial de {vehiculo.placa}')
        return redirect('historial:detalle_historial', id=vehiculo.id)

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Borrar propietario anterior',
        'objeto': f'{dueno["nombre"]} del historial de {vehiculo.placa}',
        'url_cancelar': 'historial:detalle_historial',
        'id_cancelar': vehiculo.id,
    })


# ---------------- Mantenimientos ----------------

@requiere_permiso('historial')
def agregar_mantenimiento(request, id):
    vehiculo = buscar_vehiculo(id)
    if vehiculo is None:
        return redirect('historial:lista_historiales')

    if request.method == 'POST':
        formulario = FormularioMantenimiento(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            repetido = [m for m in vehiculo.mantenimientos
                        if m['tipo'] == datos['tipo'] and m['fecha'] == datos['fecha']]
            if repetido:
                formulario.add_error('tipo', 'Ya hay un mantenimiento de ese tipo en esa fecha.')
            else:
                vehiculo.mantenimientos.append({
                    'tipo': datos['tipo'],
                    'descripcion': datos['descripcion'],
                    'fecha': datos['fecha'],
                    'costo': datos['costo'],
                })
                vehiculo.save()
                registrar_auditoria(request, 'crear', 'historial',
                                    f'Agregó {nombre_tipo(datos["tipo"]).lower()} a {vehiculo.placa}')
                return redirect('historial:detalle_historial', id=vehiculo.id)
    else:
        formulario = FormularioMantenimiento()

    return render(request, 'historial_vehiculo/formulario_registro.html', {
        'formulario': formulario,
        'vehiculo': vehiculo,
        'titulo': 'Agregar mantenimiento',
    })


@requiere_permiso('historial')
def editar_mantenimiento(request, id, indice):
    vehiculo = buscar_vehiculo(id)
    if vehiculo is None or indice >= len(vehiculo.mantenimientos):
        return redirect('historial:lista_historiales')

    mantenimiento = vehiculo.mantenimientos[indice]
    if request.method == 'POST':
        formulario = FormularioMantenimiento(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            mantenimiento['tipo'] = datos['tipo']
            mantenimiento['descripcion'] = datos['descripcion']
            mantenimiento['fecha'] = datos['fecha']
            mantenimiento['costo'] = datos['costo']
            vehiculo.save()
            registrar_auditoria(request, 'editar', 'historial', f'Modificó un mantenimiento de {vehiculo.placa}')
            return redirect('historial:detalle_historial', id=vehiculo.id)
    else:
        formulario = FormularioMantenimiento(initial=mantenimiento)

    return render(request, 'historial_vehiculo/formulario_registro.html', {
        'formulario': formulario,
        'vehiculo': vehiculo,
        'titulo': 'Modificar mantenimiento',
    })


@requiere_permiso('historial')
def eliminar_mantenimiento(request, id, indice):
    vehiculo = buscar_vehiculo(id)
    if vehiculo is None or indice >= len(vehiculo.mantenimientos):
        return redirect('historial:lista_historiales')

    mantenimiento = vehiculo.mantenimientos[indice]
    if request.method == 'POST':
        vehiculo.mantenimientos.pop(indice)
        vehiculo.save()
        registrar_auditoria(request, 'eliminar', 'historial', f'Borró un mantenimiento de {vehiculo.placa}')
        return redirect('historial:detalle_historial', id=vehiculo.id)

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Borrar mantenimiento',
        'objeto': f'{nombre_tipo(mantenimiento["tipo"])} del {mantenimiento["fecha"]:%d/%m/%Y} ({vehiculo.placa})',
        'url_cancelar': 'historial:detalle_historial',
        'id_cancelar': vehiculo.id,
    })
