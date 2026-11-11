from django.db.models import Q
from django.shortcuts import redirect, render

from clientes_vehiculos.models import Vehiculo
from clientes_vehiculos.views import buscar_vehiculo
from gestion_usuarios.sesion import registrar_auditoria, requiere_permiso
from .forms import FormularioMantenimiento, FormularioPropietario, FormularioSiniestro
from .models import Mantenimiento, Siniestro


def nombre_tipo(tipo):
    return dict(Mantenimiento.TIPOS)[tipo]


def nombre_siniestro(tipo):
    return dict(Siniestro.TIPOS)[tipo]


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
            'siniestros': len(vehiculo.siniestros),
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
    siniestros = [dict(s, indice=i, nombre_tipo=nombre_siniestro(s['tipo']))
                  for i, s in enumerate(vehiculo.siniestros)]
    siniestros.sort(key=lambda s: s['fecha'], reverse=True)

    return render(request, 'historial_vehiculo/detalle_historial.html', {
        'vehiculo': vehiculo,
        'mantenimientos': mantenimientos,
        'propietarios': propietarios,
        'siniestros': siniestros,
        'costo_total': sum(m['costo'] or 0 for m in mantenimientos),
    })


@requiere_permiso('historial')
def lista_mantenimientos(request):
    """Todos los mantenimientos de todos los vehículos, con filtro por tipo."""
    tipo = request.GET.get('tipo', '')
    filas = []
    for vehiculo in Vehiculo.objects.all():
        for indice, mantenimiento in enumerate(vehiculo.mantenimientos):
            if not tipo or mantenimiento['tipo'] == tipo:
                filas.append(dict(mantenimiento, indice=indice, vehiculo=vehiculo,
                                  nombre_tipo=nombre_tipo(mantenimiento['tipo'])))
    filas.sort(key=lambda m: m['fecha'], reverse=True)

    return render(request, 'historial_vehiculo/lista_mantenimientos.html', {
        'filas': filas,
        'tipo': tipo,
        'tipos': Mantenimiento.TIPOS,
        'total': sum(m['costo'] or 0 for m in filas),
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

    return render(request, 'historial_vehiculo/formulario_propietario.html', {
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

    return render(request, 'historial_vehiculo/formulario_propietario.html', {
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

    return render(request, 'historial_vehiculo/formulario_mantenimiento.html', {
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

    return render(request, 'historial_vehiculo/formulario_mantenimiento.html', {
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


# ---------------- Siniestros ----------------

def datos_siniestro(datos):
    return {
        'tipo': datos['tipo'],
        'fecha': datos['fecha'],
        'descripcion': datos['descripcion'],
        'costo_reparacion': datos['costo_reparacion'],
    }


@requiere_permiso('historial')
def agregar_siniestro(request, id):
    vehiculo = buscar_vehiculo(id)
    if vehiculo is None:
        return redirect('historial:lista_historiales')

    if request.method == 'POST':
        formulario = FormularioSiniestro(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            repetido = [s for s in vehiculo.siniestros
                        if s['tipo'] == datos['tipo'] and s['fecha'] == datos['fecha']]
            if repetido:
                formulario.add_error('tipo', 'Ya hay un siniestro de ese tipo en esa fecha.')
            else:
                vehiculo.siniestros.append(datos_siniestro(datos))
                vehiculo.save()
                registrar_auditoria(request, 'crear', 'historial',
                                    f'Registró un siniestro ({nombre_siniestro(datos["tipo"]).lower()}) de {vehiculo.placa}')
                return redirect('historial:detalle_historial', id=vehiculo.id)
    else:
        formulario = FormularioSiniestro()

    return render(request, 'historial_vehiculo/formulario_siniestro.html', {
        'formulario': formulario,
        'vehiculo': vehiculo,
        'titulo': 'Registrar siniestro',
    })


@requiere_permiso('historial')
def editar_siniestro(request, id, indice):
    vehiculo = buscar_vehiculo(id)
    if vehiculo is None or indice >= len(vehiculo.siniestros):
        return redirect('historial:lista_historiales')

    if request.method == 'POST':
        formulario = FormularioSiniestro(request.POST)
        if formulario.is_valid():
            vehiculo.siniestros[indice] = datos_siniestro(formulario.cleaned_data)
            vehiculo.save()
            registrar_auditoria(request, 'editar', 'historial', f'Modificó un siniestro de {vehiculo.placa}')
            return redirect('historial:detalle_historial', id=vehiculo.id)
    else:
        formulario = FormularioSiniestro(initial=vehiculo.siniestros[indice])

    return render(request, 'historial_vehiculo/formulario_siniestro.html', {
        'formulario': formulario,
        'vehiculo': vehiculo,
        'titulo': 'Modificar siniestro',
    })


@requiere_permiso('historial')
def eliminar_siniestro(request, id, indice):
    vehiculo = buscar_vehiculo(id)
    if vehiculo is None or indice >= len(vehiculo.siniestros):
        return redirect('historial:lista_historiales')

    siniestro = vehiculo.siniestros[indice]
    if request.method == 'POST':
        vehiculo.siniestros.pop(indice)
        vehiculo.save()
        registrar_auditoria(request, 'eliminar', 'historial', f'Borró un siniestro de {vehiculo.placa}')
        return redirect('historial:detalle_historial', id=vehiculo.id)

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Borrar siniestro',
        'objeto': f'{nombre_siniestro(siniestro["tipo"])} del {siniestro["fecha"]:%d/%m/%Y} ({vehiculo.placa})',
        'url_cancelar': 'historial:detalle_historial',
        'id_cancelar': vehiculo.id,
    })
