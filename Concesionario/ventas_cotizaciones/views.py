import datetime

from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse

from clientes_vehiculos.models import Cliente, Vehiculo
from clientes_vehiculos.views import actualizar_estado_vehiculo, cotizaciones_de_placa, todas_las_cotizaciones
from gestion_usuarios.sesion import registrar_auditoria, requiere_permiso, vendedor_actual
from gestion_usuarios.views import actualizar_metas
from pagos_facturacion.models import Factura
from .forms import (FORMAS_PAGO, FormularioCondicion, FormularioCotizacion, FormularioDescuento,
                    FormularioEditarCotizacion, FormularioPlantilla, FormularioVenta)
from .models import Cotizacion, PlantillaCotizacion


def buscar_plantilla(id):
    try:
        return PlantillaCotizacion.objects.get(id=id)
    except PlantillaCotizacion.DoesNotExist:
        return None


def buscar_cotizacion(id):
    """Devuelve la cotización con su cliente adjunto en .cliente (o None)."""
    cotizacion = Cotizacion.objects.filter(id=id).first()
    if cotizacion is None:
        return None
    cotizacion.cliente = Cliente.objects.filter(id=cotizacion.id_cliente).first()
    if cotizacion.cliente is None:
        return None
    return cotizacion


def texto_cotizacion(cotizacion):
    vehiculo, cliente = cotizacion.vehiculo, cotizacion.cliente
    return (f'{vehiculo["marca"]} {vehiculo["modelo"]} ({vehiculo["placa"]}) '
            f'para {cliente.nombre} {cliente.apellido}')


# =====================================================================
# Plantillas de cotización (colección plantillasCotizacion)
# =====================================================================

@requiere_permiso('ventas')
def lista_plantillas(request):
    plantillas = PlantillaCotizacion.objects.all().order_by('nombre')
    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        plantillas = plantillas.filter(Q(nombre__icontains=busqueda) | Q(descripcion__icontains=busqueda))
    return render(request, 'ventas_cotizaciones/lista_plantillas.html', {
        'plantillas': plantillas,
        'busqueda': busqueda,
        'total': PlantillaCotizacion.objects.count(),
    })


@requiere_permiso('ventas')
def crear_plantilla(request):
    if request.method == 'POST':
        formulario = FormularioPlantilla(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            plantilla = PlantillaCotizacion.objects.create(
                nombre=datos['nombre'],
                descripcion=datos['descripcion'],
                activa=datos['activa'],
                creado_por=vendedor_actual(request),
                condiciones=[],
                descuentos=[],
                notas_adicionales=datos['notas_adicionales'],
            )
            registrar_auditoria(request, 'crear', 'ventas', f'Creó la plantilla {plantilla.nombre}')
            return redirect('ventas:detalle_plantilla', id=plantilla.id)
    else:
        formulario = FormularioPlantilla()

    return render(request, 'ventas_cotizaciones/formulario_plantilla.html', {
        'formulario': formulario,
        'titulo': 'Nueva plantilla de cotización',
    })


@requiere_permiso('ventas')
def detalle_plantilla(request, id):
    plantilla = buscar_plantilla(id)
    if plantilla is None:
        return redirect('ventas:lista_plantillas')

    condiciones = [dict(c, indice=i) for i, c in enumerate(plantilla.condiciones)]
    condiciones.sort(key=lambda c: c['orden'])
    return render(request, 'ventas_cotizaciones/detalle_plantilla.html', {
        'plantilla': plantilla,
        'condiciones': condiciones,
        'descuentos': [dict(d, indice=i) for i, d in enumerate(plantilla.descuentos)],
    })


@requiere_permiso('ventas')
def editar_plantilla(request, id):
    plantilla = buscar_plantilla(id)
    if plantilla is None:
        return redirect('ventas:lista_plantillas')

    if request.method == 'POST':
        formulario = FormularioPlantilla(request.POST, plantilla=plantilla)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            plantilla.nombre = datos['nombre']
            plantilla.descripcion = datos['descripcion']
            plantilla.activa = datos['activa']
            plantilla.notas_adicionales = datos['notas_adicionales']
            plantilla.save()
            registrar_auditoria(request, 'editar', 'ventas', f'Editó la plantilla {plantilla.nombre}')
            return redirect('ventas:detalle_plantilla', id=plantilla.id)
    else:
        formulario = FormularioPlantilla(plantilla=plantilla, initial={
            'nombre': plantilla.nombre,
            'descripcion': plantilla.descripcion,
            'activa': plantilla.activa,
            'notas_adicionales': plantilla.notas_adicionales,
        })

    return render(request, 'ventas_cotizaciones/formulario_plantilla.html', {
        'formulario': formulario,
        'titulo': f'Editar plantilla {plantilla.nombre}',
        'plantilla': plantilla,
    })


@requiere_permiso('ventas')
def eliminar_plantilla(request, id):
    plantilla = buscar_plantilla(id)
    if plantilla is None:
        return redirect('ventas:lista_plantillas')

    if request.method == 'POST':
        plantilla.delete()
        registrar_auditoria(request, 'eliminar', 'ventas', f'Eliminó la plantilla {plantilla.nombre}')
        return redirect('ventas:lista_plantillas')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar plantilla',
        'objeto': plantilla.nombre,
        'advertencia': 'Las cotizaciones que ya usaron sus descuentos no cambian.',
        'url_cancelar': 'ventas:detalle_plantilla',
        'id_cancelar': plantilla.id,
    })


@requiere_permiso('ventas')
def agregar_condicion(request, id):
    plantilla = buscar_plantilla(id)
    if plantilla is None:
        return redirect('ventas:lista_plantillas')

    if request.method == 'POST':
        formulario = FormularioCondicion(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            if any(c['titulo'].lower() == datos['titulo'].lower() for c in plantilla.condiciones):
                formulario.add_error('titulo', 'La plantilla ya tiene una condición con ese título.')
            else:
                plantilla.condiciones.append({
                    'titulo': datos['titulo'],
                    'contenido': datos['contenido'],
                    'orden': datos['orden'],
                })
                plantilla.save()
                registrar_auditoria(request, 'crear', 'ventas', f'Agregó una condición a {plantilla.nombre}')
                return redirect('ventas:detalle_plantilla', id=plantilla.id)
    else:
        formulario = FormularioCondicion(initial={'orden': len(plantilla.condiciones) + 1})

    return render(request, 'ventas_cotizaciones/formulario_detalle_plantilla.html', {
        'formulario': formulario,
        'plantilla': plantilla,
        'titulo': 'Agregar condición',
    })


@requiere_permiso('ventas')
def eliminar_condicion(request, id, indice):
    plantilla = buscar_plantilla(id)
    if plantilla and request.method == 'POST' and indice < len(plantilla.condiciones):
        plantilla.condiciones.pop(indice)
        plantilla.save()
        registrar_auditoria(request, 'eliminar', 'ventas', f'Quitó una condición de {plantilla.nombre}')
    return redirect('ventas:detalle_plantilla', id=id)


@requiere_permiso('ventas')
def agregar_descuento(request, id):
    plantilla = buscar_plantilla(id)
    if plantilla is None:
        return redirect('ventas:lista_plantillas')

    if request.method == 'POST':
        formulario = FormularioDescuento(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            if any(d['nombre'].lower() == datos['nombre'].lower() for d in plantilla.descuentos):
                formulario.add_error('nombre', 'La plantilla ya tiene un descuento con ese nombre.')
            else:
                plantilla.descuentos.append({
                    'nombre': datos['nombre'],
                    'porcentaje': datos['porcentaje'],
                    'descripcion': datos['descripcion'],
                })
                plantilla.save()
                registrar_auditoria(request, 'crear', 'ventas', f'Agregó un descuento a {plantilla.nombre}')
                return redirect('ventas:detalle_plantilla', id=plantilla.id)
    else:
        formulario = FormularioDescuento()

    return render(request, 'ventas_cotizaciones/formulario_detalle_plantilla.html', {
        'formulario': formulario,
        'plantilla': plantilla,
        'titulo': 'Agregar descuento',
    })


@requiere_permiso('ventas')
def eliminar_descuento(request, id, indice):
    plantilla = buscar_plantilla(id)
    if plantilla and request.method == 'POST' and indice < len(plantilla.descuentos):
        plantilla.descuentos.pop(indice)
        plantilla.save()
        registrar_auditoria(request, 'eliminar', 'ventas', f'Quitó un descuento de {plantilla.nombre}')
    return redirect('ventas:detalle_plantilla', id=id)


# =====================================================================
# Cotizaciones (colección cotizaciones)
# =====================================================================

@requiere_permiso('ventas')
def lista_cotizaciones(request):
    cotizaciones = todas_las_cotizaciones()
    busqueda = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '')

    conteo = {'todas': len(cotizaciones)}
    for valor in ['pendiente', 'aprobada', 'rechazada']:
        conteo[valor] = len([c for c in cotizaciones if c.estado == valor])

    if estado:
        cotizaciones = [c for c in cotizaciones if c.estado == estado]
    if busqueda:
        cotizaciones = [c for c in cotizaciones if c.cliente and busqueda.lower() in (
            f'{c.cliente.nombre} {c.cliente.apellido} {c.cliente.cedula} '
            f'{c.vehiculo["marca"]} {c.vehiculo["modelo"]} {c.vehiculo["placa"]}').lower()]

    return render(request, 'ventas_cotizaciones/lista_cotizaciones.html', {
        'cotizaciones': cotizaciones,
        'busqueda': busqueda,
        'estado': estado,
        'conteo': conteo,
    })


@requiere_permiso('ventas')
def crear_cotizacion(request):
    if request.method == 'POST':
        formulario = FormularioCotizacion(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            cliente = Cliente.objects.get(id=int(datos['cliente']))
            vehiculo = Vehiculo.objects.get(placa=datos['vehiculo'])

            abierta = [c for c in Cotizacion.objects.filter(id_cliente=cliente.id)
                       if c.vehiculo['placa'] == vehiculo.placa and c.estado != 'rechazada' and not c.venta]
            if abierta:
                formulario.add_error('vehiculo', 'El cliente ya tiene una cotización abierta para este vehículo.')
            else:
                notas = datos['notas']
                porcentaje = 0
                if datos['descuento']:
                    id_plantilla, posicion = datos['descuento'].split('-')
                    plantilla = buscar_plantilla(int(id_plantilla))
                    descuento = plantilla.descuentos[int(posicion)]
                    porcentaje = descuento['porcentaje']
                    notas = (f'Descuento "{descuento["nombre"]}" ({porcentaje:g} %) de la plantilla '
                             f'{plantilla.nombre}.\n{notas}').strip()

                precio = datos['precio_ofertado']
                if precio is None:
                    precio = round((vehiculo.precio or 0) * (1 - porcentaje / 100))

                cotizacion = Cotizacion.objects.create(
                    id_cliente=cliente.id,
                    vehiculo={
                        'marca': vehiculo.marca,
                        'modelo': vehiculo.modelo,
                        'anio': vehiculo.anio,
                        'placa': vehiculo.placa,
                        'precio': vehiculo.precio,
                    },
                    vendedor=vendedor_actual(request),
                    precio_ofertado=float(precio),
                    fecha=datos['fecha'],
                    estado='pendiente',
                    notas=notas,
                    venta=None,
                )
                cotizacion.cliente = cliente
                registrar_auditoria(request, 'crear', 'ventas', f'Cotizó {texto_cotizacion(cotizacion)}')
                return redirect('ventas:detalle_cotizacion', id=cotizacion.id)
    else:
        formulario = FormularioCotizacion(initial={
            'fecha': datetime.date.today(),
            'cliente': request.GET.get('cliente', ''),
            'vehiculo': request.GET.get('placa', ''),
        })

    return render(request, 'ventas_cotizaciones/formulario_cotizacion.html', {
        'formulario': formulario,
        'titulo': 'Nueva cotización',
    })


@requiere_permiso('ventas')
def detalle_cotizacion(request, id):
    cotizacion = buscar_cotizacion(id)
    if cotizacion is None:
        return redirect('ventas:lista_cotizaciones')

    factura = None
    if cotizacion.venta and cotizacion.venta['numero_factura']:
        factura = Factura.objects.filter(numero_factura=cotizacion.venta['numero_factura']).first()

    precio_lista = cotizacion.vehiculo['precio'] or 0
    return render(request, 'ventas_cotizaciones/detalle_cotizacion.html', {
        'cliente': cotizacion.cliente,
        'cotizacion': cotizacion,
        'factura': factura,
        'ahorro': precio_lista - (cotizacion.precio_ofertado or 0),
        'formas_pago': dict(FORMAS_PAGO),
    })


@requiere_permiso('ventas')
def editar_cotizacion(request, id):
    cotizacion = buscar_cotizacion(id)
    if cotizacion is None:
        return redirect('ventas:lista_cotizaciones')

    vendida = bool(cotizacion.venta)
    if request.method == 'POST':
        formulario = FormularioEditarCotizacion(request.POST, vendida=vendida, initial={
            'precio_ofertado': cotizacion.precio_ofertado,
            'estado': cotizacion.estado,
        })
        if formulario.is_valid():
            datos = formulario.cleaned_data
            cotizacion.precio_ofertado = datos['precio_ofertado']
            cotizacion.fecha = datos['fecha']
            cotizacion.estado = datos['estado']
            cotizacion.notas = datos['notas']
            cotizacion.save()
            actualizar_estado_vehiculo(cotizacion.vehiculo['placa'])
            registrar_auditoria(request, 'editar', 'ventas', f'Editó la cotización {texto_cotizacion(cotizacion)}')
            return redirect('ventas:detalle_cotizacion', id=cotizacion.id)
    else:
        formulario = FormularioEditarCotizacion(vendida=vendida, initial={
            'precio_ofertado': cotizacion.precio_ofertado,
            'fecha': cotizacion.fecha,
            'estado': cotizacion.estado,
            'notas': cotizacion.notas,
        })

    return render(request, 'ventas_cotizaciones/formulario_cotizacion.html', {
        'formulario': formulario,
        'titulo': 'Editar cotización',
        'cliente': cotizacion.cliente,
        'cotizacion': cotizacion,
    })


@requiere_permiso('ventas')
def cambiar_estado_cotizacion(request, id, estado):
    cotizacion = buscar_cotizacion(id)
    if cotizacion and request.method == 'POST' and not cotizacion.venta \
            and estado in ('pendiente', 'aprobada', 'rechazada'):
        cotizacion.estado = estado
        cotizacion.save()
        actualizar_estado_vehiculo(cotizacion.vehiculo['placa'])
        registrar_auditoria(request, 'editar', 'ventas',
                            f'Marcó como {estado} la cotización {texto_cotizacion(cotizacion)}')
    return redirect('ventas:detalle_cotizacion', id=id)


@requiere_permiso('ventas')
def eliminar_cotizacion(request, id):
    cotizacion = buscar_cotizacion(id)
    if cotizacion is None:
        return redirect('ventas:lista_cotizaciones')

    vendida = bool(cotizacion.venta)
    if request.method == 'POST' and not vendida:
        cotizacion.delete()
        actualizar_estado_vehiculo(cotizacion.vehiculo['placa'])
        registrar_auditoria(request, 'eliminar', 'ventas', f'Eliminó la cotización {texto_cotizacion(cotizacion)}')
        return redirect('ventas:lista_cotizaciones')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar cotización',
        'objeto': texto_cotizacion(cotizacion),
        'bloqueado': vendida,
        'motivo': 'La cotización ya tiene una venta. Primero elimina la venta.',
        'url_volver': reverse('ventas:detalle_cotizacion', args=[id]),
    })


# =====================================================================
# Ventas (embebidas en la cotización)
# =====================================================================

@requiere_permiso('ventas')
def registrar_venta(request, id):
    cotizacion = buscar_cotizacion(id)
    if cotizacion is None:
        return redirect('ventas:lista_cotizaciones')
    if cotizacion.venta or cotizacion.estado != 'aprobada':
        return redirect('ventas:detalle_cotizacion', id=id)

    placa = cotizacion.vehiculo['placa']
    if request.method == 'POST':
        formulario = FormularioVenta(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            if any(c.venta for c in cotizaciones_de_placa(placa)):
                formulario.add_error(None, 'Este vehículo ya fue vendido en otra cotización.')
            else:
                cotizacion.venta = {
                    'fecha_venta': datos['fecha_venta'],
                    'precio_final': datos['precio_final'],
                    'forma_pago': datos['forma_pago'],
                    'numero_factura': '',
                }
                cotizacion.save()
                actualizar_estado_vehiculo(placa)
                actualizar_metas(cotizacion.vendedor['nombre_usuario'])
                registrar_auditoria(request, 'crear', 'ventas', f'Registró la venta de {texto_cotizacion(cotizacion)}')
                return redirect('ventas:detalle_cotizacion', id=id)
    else:
        formulario = FormularioVenta(initial={
            'fecha_venta': datetime.date.today(),
            'precio_final': cotizacion.precio_ofertado,
        })

    return render(request, 'ventas_cotizaciones/formulario_venta.html', {
        'formulario': formulario,
        'cliente': cotizacion.cliente,
        'cotizacion': cotizacion,
    })


@requiere_permiso('ventas')
def lista_ventas(request):
    ventas = [c for c in todas_las_cotizaciones() if c.venta]
    forma = request.GET.get('forma', '')
    if forma:
        ventas = [v for v in ventas if v.venta['forma_pago'] == forma]
    ventas.sort(key=lambda v: v.venta['fecha_venta'], reverse=True)

    return render(request, 'ventas_cotizaciones/lista_ventas.html', {
        'ventas': ventas,
        'forma': forma,
        'formas_pago': FORMAS_PAGO,
        'total': sum(v.venta['precio_final'] or 0 for v in ventas),
        'sin_factura': len([v for v in ventas if not v.venta['numero_factura']]),
    })


@requiere_permiso('ventas')
def eliminar_venta(request, id):
    cotizacion = buscar_cotizacion(id)
    if cotizacion is None or not cotizacion.venta:
        return redirect('ventas:lista_ventas')

    facturada = bool(cotizacion.venta['numero_factura'])
    if request.method == 'POST' and not facturada:
        cotizacion.venta = None
        cotizacion.save()
        actualizar_estado_vehiculo(cotizacion.vehiculo['placa'])
        actualizar_metas(cotizacion.vendedor['nombre_usuario'])
        registrar_auditoria(request, 'eliminar', 'ventas', f'Eliminó la venta de {texto_cotizacion(cotizacion)}')
        return redirect('ventas:detalle_cotizacion', id=id)

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar venta',
        'objeto': f'la venta de {texto_cotizacion(cotizacion)}',
        'bloqueado': facturada,
        'motivo': f'La venta tiene la factura {cotizacion.venta["numero_factura"]}. Primero anula o elimina la factura.',
        'advertencia': 'La cotización vuelve a quedar aprobada y el vehículo reservado.',
        'url_volver': reverse('ventas:detalle_cotizacion', args=[id]),
    })
