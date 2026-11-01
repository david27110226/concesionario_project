from django.db.models import Q
from django.shortcuts import redirect, render

from clientes_vehiculos.models import Vehiculo
from .forms import (FormularioHistorial, FormularioMantenimiento, FormularioObservaciones,
                    FormularioPropietario, FormularioTaller)
from .models import TIPOS_MANTENIMIENTO, HistorialVehiculo, Taller


def buscar_historial(id):
    try:
        return HistorialVehiculo.objects.get(id=id)
    except HistorialVehiculo.DoesNotExist:
        return None


def buscar_taller(id):
    try:
        return Taller.objects.get(id=id)
    except Taller.DoesNotExist:
        return None


# ---------------- Historiales ----------------

def lista_historiales(request):
    historiales = HistorialVehiculo.objects.all().order_by('-id')
    busqueda = request.GET.get('q', '').strip().upper()
    if busqueda:
        historiales = [h for h in historiales
                       if busqueda in h.vehiculo['placa'] or busqueda in h.vehiculo['marca'].upper()
                       or busqueda in h.vehiculo['modelo'].upper()]

    total_mantenimientos = sum(len(h.mantenimientos) for h in historiales)
    inversion = sum(h.costo_total() for h in historiales)

    return render(request, 'historial_vehiculo/lista_historiales.html', {
        'historiales': historiales,
        'busqueda': request.GET.get('q', ''),
        'total_mantenimientos': total_mantenimientos,
        'inversion': inversion,
    })


def crear_historial(request):
    if request.method == 'POST':
        formulario = FormularioHistorial(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            vehiculo = Vehiculo.objects.filter(placa=datos['vehiculo']).first()
            if vehiculo is None:
                formulario.add_error('vehiculo', 'El vehículo no existe.')
            else:
                historial = HistorialVehiculo.objects.create(
                    vehiculo=vehiculo.resumen(),
                    observaciones=datos['observaciones'],
                    propietarios_anteriores=[],
                    mantenimientos=[],
                )
                return redirect('historial:detalle_historial', id=historial.id)
    else:
        formulario = FormularioHistorial(initial={'vehiculo': request.GET.get('placa', '')})

    return render(request, 'historial_vehiculo/formulario_historial.html', {
        'formulario': formulario,
        'titulo': 'Abrir historial de vehículo',
    })


def detalle_historial(request, id):
    historial = buscar_historial(id)
    if historial is None:
        return redirect('historial:lista_historiales')

    nombres_tipo = dict(TIPOS_MANTENIMIENTO)
    # Se ordenan del más reciente al más antiguo sin perder la posición original (para eliminar)
    mantenimientos = [
        dict(m, indice=i, nombre_tipo=nombres_tipo.get(m['tipo'], m['tipo']))
        for i, m in enumerate(historial.mantenimientos)
    ]
    mantenimientos.sort(key=lambda m: m['fecha'], reverse=True)
    propietarios = [dict(p, indice=i) for i, p in enumerate(historial.propietarios_anteriores)]

    return render(request, 'historial_vehiculo/detalle_historial.html', {
        'historial': historial,
        'vehiculo': Vehiculo.objects.filter(placa=historial.vehiculo['placa']).first(),
        'mantenimientos': mantenimientos,
        'propietarios': propietarios,
        'costo_total': historial.costo_total(),
    })


def editar_historial(request, id):
    historial = buscar_historial(id)
    if historial is None:
        return redirect('historial:lista_historiales')

    if request.method == 'POST':
        formulario = FormularioObservaciones(request.POST)
        if formulario.is_valid():
            historial.observaciones = formulario.cleaned_data['observaciones']
            historial.save()
            return redirect('historial:detalle_historial', id=historial.id)
    else:
        formulario = FormularioObservaciones(initial={'observaciones': historial.observaciones})

    return render(request, 'historial_vehiculo/formulario_historial.html', {
        'formulario': formulario,
        'titulo': f"Editar historial {historial.vehiculo['placa']}",
        'historial': historial,
    })


def eliminar_historial(request, id):
    historial = buscar_historial(id)
    if historial is None:
        return redirect('historial:lista_historiales')

    if request.method == 'POST':
        historial.delete()
        return redirect('historial:lista_historiales')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar historial',
        'objeto': f"Historial del vehículo {historial.vehiculo['placa']}",
        'advertencia': f'Se perderán {len(historial.mantenimientos)} mantenimientos registrados.',
        'url_cancelar': 'historial:detalle_historial',
        'id_cancelar': historial.id,
    })


def agregar_mantenimiento(request, id):
    historial = buscar_historial(id)
    if historial is None:
        return redirect('historial:lista_historiales')

    if request.method == 'POST':
        formulario = FormularioMantenimiento(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            historial.mantenimientos.append({
                'tipo': datos['tipo'],
                'descripcion': datos['descripcion'],
                'fecha': datos['fecha'],
                'kilometraje': datos['kilometraje'],
                'costo': datos['costo'],
                'taller': datos['taller'],
            })
            historial.save()
            # El kilometraje del vehículo se actualiza si el mantenimiento reporta uno mayor
            vehiculo = Vehiculo.objects.filter(placa=historial.vehiculo['placa']).first()
            if vehiculo and datos['kilometraje'] > vehiculo.kilometraje:
                Vehiculo.objects.filter(id=vehiculo.id).update(kilometraje=datos['kilometraje'])
            return redirect('historial:detalle_historial', id=historial.id)
    else:
        formulario = FormularioMantenimiento()

    return render(request, 'historial_vehiculo/formulario_registro.html', {
        'formulario': formulario,
        'titulo': 'Registrar mantenimiento',
        'historial': historial,
    })


def eliminar_mantenimiento(request, id, indice):
    historial = buscar_historial(id)
    if historial is not None and request.method == 'POST' and 0 <= indice < len(historial.mantenimientos):
        historial.mantenimientos.pop(indice)
        historial.save()
    return redirect('historial:detalle_historial', id=id)


def agregar_propietario(request, id):
    historial = buscar_historial(id)
    if historial is None:
        return redirect('historial:lista_historiales')

    if request.method == 'POST':
        formulario = FormularioPropietario(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            historial.propietarios_anteriores.append({
                'nombre': datos['nombre'],
                'documento': datos['documento'],
                'fecha_inicio': datos['fecha_inicio'],
                'fecha_fin': datos['fecha_fin'],
            })
            historial.save()
            return redirect('historial:detalle_historial', id=historial.id)
    else:
        formulario = FormularioPropietario()

    return render(request, 'historial_vehiculo/formulario_registro.html', {
        'formulario': formulario,
        'titulo': 'Agregar propietario anterior',
        'historial': historial,
    })


def eliminar_propietario(request, id, indice):
    historial = buscar_historial(id)
    if historial is not None and request.method == 'POST' and 0 <= indice < len(historial.propietarios_anteriores):
        historial.propietarios_anteriores.pop(indice)
        historial.save()
    return redirect('historial:detalle_historial', id=id)


# ---------------- Talleres ----------------

def lista_talleres(request):
    talleres = Taller.objects.all().order_by('nombre')
    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        talleres = talleres.filter(Q(nombre__icontains=busqueda) | Q(ciudad__icontains=busqueda))

    historiales = list(HistorialVehiculo.objects.all())
    for taller in talleres:
        servicios = [m for h in historiales for m in h.mantenimientos if m['taller'] == taller.nombre]
        taller.servicios = len(servicios)
        taller.facturado = sum(m['costo'] for m in servicios)

    return render(request, 'historial_vehiculo/lista_talleres.html', {
        'talleres': talleres,
        'busqueda': busqueda,
    })


def guardar_taller(request, id=None):
    taller = buscar_taller(id) if id else None
    if id and taller is None:
        return redirect('historial:lista_talleres')

    if request.method == 'POST':
        formulario = FormularioTaller(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            repetidos = Taller.objects.filter(nombre=datos['nombre'])
            if taller:
                repetidos = repetidos.exclude(id=taller.id)
            if repetidos.exists():
                formulario.add_error('nombre', 'Ya existe un taller con ese nombre.')
            elif taller is None:
                Taller.objects.create(**datos)
                return redirect('historial:lista_talleres')
            else:
                Taller.objects.filter(id=taller.id).update(**datos)
                # Si cambia el nombre, se actualiza en los mantenimientos que lo tienen embebido
                if datos['nombre'] != taller.nombre:
                    for historial in HistorialVehiculo.objects.all():
                        cambiados = [m for m in historial.mantenimientos if m['taller'] == taller.nombre]
                        for mantenimiento in cambiados:
                            mantenimiento['taller'] = datos['nombre']
                        if cambiados:
                            historial.save()
                return redirect('historial:lista_talleres')
    else:
        formulario = FormularioTaller(initial={
            'nombre': taller.nombre, 'nit': taller.nit, 'telefono': taller.telefono,
            'ciudad': taller.ciudad, 'especialidad': taller.especialidad,
        } if taller else None)

    return render(request, 'historial_vehiculo/formulario_taller.html', {
        'formulario': formulario,
        'titulo': f'Editar taller {taller.nombre}' if taller else 'Nuevo taller',
    })


def crear_taller(request):
    return guardar_taller(request)


def editar_taller(request, id):
    return guardar_taller(request, id)


def eliminar_taller(request, id):
    taller = buscar_taller(id)
    if taller is None:
        return redirect('historial:lista_talleres')

    if request.method == 'POST':
        taller.delete()
        return redirect('historial:lista_talleres')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar taller',
        'objeto': taller.nombre,
        'advertencia': 'Los mantenimientos ya registrados conservan el nombre del taller.',
        'url_cancelar': 'historial:lista_talleres',
    })
