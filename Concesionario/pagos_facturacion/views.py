import datetime

from django.db.models import Q
from django.shortcuts import redirect, render

from clientes_vehiculos.models import Cliente
from gestion_usuarios.sesion import registrar_auditoria, requiere_permiso
from ventas_cotizaciones.models import Cotizacion
from .forms import FormularioEditarFactura, FormularioFactura, FormularioPago
from .models import DetallePago, Factura


def buscar_factura(id):
    try:
        return Factura.objects.get(id=id)
    except Factura.DoesNotExist:
        return None


def total_pagado(factura):
    return sum(p['monto'] for p in factura.pagos)


def saldo(factura):
    return max(factura.total - total_pagado(factura), 0)


def actualizar_estado(factura):
    if factura.estado != 'anulada':
        factura.estado = 'pagada' if saldo(factura) < 1 else 'emitida'


def siguiente_numero():
    numeros = [int(f.numero_factura.split('-')[1]) for f in Factura.objects.all()]
    return f'FAC-{max(numeros, default=0) + 1:05d}'


def asignar_numero_a_venta(factura, numero):
    """Guarda (o borra) el número de factura dentro de la venta de la cotización."""
    for cotizacion in Cotizacion.objects.all():
        venta = cotizacion.venta
        if venta and venta['numero_factura'] == factura.numero_factura:
            venta['numero_factura'] = numero
            cotizacion.save()
            return


# ---------------- Facturas ----------------

@requiere_permiso('pagos')
def lista_facturas(request):
    facturas = Factura.objects.all().order_by('-id')
    busqueda = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '')
    if busqueda:
        facturas = facturas.filter(
            Q(numero_factura__icontains=busqueda) | Q(nombre_cliente__icontains=busqueda) |
            Q(cedula_cliente__icontains=busqueda) | Q(placa_vehiculo__icontains=busqueda)
        )
    if estado:
        facturas = facturas.filter(estado=estado)

    filas = [{'factura': f, 'pagado': total_pagado(f), 'saldo': saldo(f)} for f in facturas]
    return render(request, 'pagos_facturacion/lista_facturas.html', {
        'filas': filas,
        'busqueda': busqueda,
        'estado': estado,
        'estados': Factura.ESTADOS_FACTURA,
        'total': Factura.objects.count(),
    })


@requiere_permiso('pagos')
def crear_factura(request):
    if request.method == 'POST':
        formulario = FormularioFactura(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            cotizacion = Cotizacion.objects.get(id=int(datos['venta']))
            cliente = Cliente.objects.get(id=cotizacion.id_cliente)
            subtotal = cotizacion.venta['precio_final'] or 0
            impuesto = round(subtotal * datos['iva_porcentaje'] / 100)

            factura = Factura.objects.create(
                numero_factura=siguiente_numero(),
                cedula_cliente=cliente.cedula,
                nombre_cliente=f'{cliente.nombre} {cliente.apellido}',
                placa_vehiculo=cotizacion.vehiculo['placa'],
                subtotal=subtotal,
                impuesto_iva=impuesto,
                total=subtotal + impuesto,
                estado='emitida',
                pagos=[],
            )
            cotizacion.venta['numero_factura'] = factura.numero_factura
            cotizacion.save()
            registrar_auditoria(request, 'crear', 'pagos', f'Generó la factura {factura.numero_factura}')
            return redirect('pagos:detalle_factura', id=factura.id)
    else:
        formulario = FormularioFactura(initial={'venta': request.GET.get('venta', '')})

    return render(request, 'pagos_facturacion/formulario_factura.html', {
        'formulario': formulario,
        'titulo': 'Nueva factura',
    })


@requiere_permiso('pagos')
def detalle_factura(request, id):
    factura = buscar_factura(id)
    if factura is None:
        return redirect('pagos:lista_facturas')

    pagado = total_pagado(factura)
    medios = dict(DetallePago.TIPOS_PAGO)
    pagos = [dict(p, indice=i, medio=medios[p['tipo_pago']]) for i, p in enumerate(factura.pagos)]
    return render(request, 'pagos_facturacion/detalle_factura.html', {
        'factura': factura,
        'pagos': pagos,
        'pagado': pagado,
        'saldo': saldo(factura),
        'porcentaje': min(round(pagado * 100 / factura.total), 100) if factura.total else 0,
        'iva_porcentaje': round(factura.impuesto_iva * 100 / factura.subtotal, 2) if factura.subtotal else 0,
    })


@requiere_permiso('pagos')
def editar_factura(request, id):
    factura = buscar_factura(id)
    if factura is None or factura.estado == 'anulada':
        return redirect('pagos:lista_facturas')

    pagado = total_pagado(factura)
    if request.method == 'POST':
        formulario = FormularioEditarFactura(request.POST, pagado=pagado)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            factura.subtotal = datos['subtotal']
            factura.impuesto_iva = round(datos['subtotal'] * datos['iva_porcentaje'] / 100)
            factura.total = factura.subtotal + factura.impuesto_iva
            actualizar_estado(factura)
            factura.save()
            registrar_auditoria(request, 'editar', 'pagos', f'Editó la factura {factura.numero_factura}')
            return redirect('pagos:detalle_factura', id=factura.id)
    else:
        formulario = FormularioEditarFactura(pagado=pagado, initial={
            'subtotal': factura.subtotal,
            'iva_porcentaje': round(factura.impuesto_iva * 100 / factura.subtotal, 2),
        })

    return render(request, 'pagos_facturacion/formulario_factura.html', {
        'formulario': formulario,
        'titulo': f'Editar factura {factura.numero_factura}',
        'factura': factura,
    })


@requiere_permiso('pagos')
def anular_factura(request, id):
    factura = buscar_factura(id)
    if factura and request.method == 'POST' and factura.estado != 'anulada':
        # La venta queda libre para volver a facturarse
        asignar_numero_a_venta(factura, '')
        factura.estado = 'anulada'
        factura.save()
        registrar_auditoria(request, 'editar', 'pagos', f'Anuló la factura {factura.numero_factura}')
    return redirect('pagos:detalle_factura', id=id)


@requiere_permiso('pagos')
def eliminar_factura(request, id):
    factura = buscar_factura(id)
    if factura is None:
        return redirect('pagos:lista_facturas')

    con_pagos = bool(factura.pagos)
    if request.method == 'POST' and not con_pagos:
        asignar_numero_a_venta(factura, '')
        factura.delete()
        registrar_auditoria(request, 'eliminar', 'pagos', f'Eliminó la factura {factura.numero_factura}')
        return redirect('pagos:lista_facturas')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar factura',
        'objeto': f'la factura {factura.numero_factura} de {factura.nombre_cliente}',
        'bloqueado': con_pagos,
        'motivo': 'La factura tiene pagos registrados. Puedes anularla en lugar de eliminarla.',
        'advertencia': 'La venta quedará sin factura y se podrá volver a facturar.',
        'url_cancelar': 'pagos:detalle_factura',
        'id_cancelar': factura.id,
    })


# ---------------- Pagos (embebidos en la factura) ----------------

def datos_pago(datos):
    return {
        'tipo_pago': datos['tipo_pago'],
        'forma_pago': datos['forma_pago'],
        'monto': datos['monto'],
        'fecha_pago': datos['fecha_pago'],
        'numero_referencia': datos['numero_referencia'],
        'observaciones': datos['observaciones'],
    }


def referencia_repetida(factura, referencia, omitir=None):
    return referencia and any(
        i != omitir and p['numero_referencia'] == referencia for i, p in enumerate(factura.pagos))


@requiere_permiso('pagos')
def registrar_pago(request, id):
    factura = buscar_factura(id)
    if factura is None or factura.estado != 'emitida':
        return redirect('pagos:detalle_factura', id=id)

    if request.method == 'POST':
        formulario = FormularioPago(request.POST, maximo=saldo(factura))
        if formulario.is_valid():
            datos = formulario.cleaned_data
            if referencia_repetida(factura, datos['numero_referencia']):
                formulario.add_error('numero_referencia', 'Ya hay un pago con esa referencia en la factura.')
            else:
                factura.pagos.append(datos_pago(datos))
                actualizar_estado(factura)
                factura.save()
                registrar_auditoria(request, 'crear', 'pagos', f'Registró un pago en la factura {factura.numero_factura}')
                return redirect('pagos:detalle_factura', id=factura.id)
    else:
        formulario = FormularioPago(maximo=saldo(factura), initial={
            'monto': saldo(factura),
            'fecha_pago': datetime.date.today(),
        })

    return render(request, 'pagos_facturacion/formulario_pago.html', {
        'formulario': formulario,
        'factura': factura,
        'titulo': 'Registrar pago',
    })


@requiere_permiso('pagos')
def editar_pago(request, id, indice):
    factura = buscar_factura(id)
    if factura is None or factura.estado == 'anulada' or indice >= len(factura.pagos):
        return redirect('pagos:detalle_factura', id=id)

    pago = factura.pagos[indice]
    maximo = saldo(factura) + pago['monto']
    if request.method == 'POST':
        formulario = FormularioPago(request.POST, maximo=maximo)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            if referencia_repetida(factura, datos['numero_referencia'], omitir=indice):
                formulario.add_error('numero_referencia', 'Ya hay un pago con esa referencia en la factura.')
            else:
                factura.pagos[indice] = datos_pago(datos)
                actualizar_estado(factura)
                factura.save()
                registrar_auditoria(request, 'editar', 'pagos', f'Editó un pago de la factura {factura.numero_factura}')
                return redirect('pagos:detalle_factura', id=factura.id)
    else:
        formulario = FormularioPago(maximo=maximo, initial=pago)

    return render(request, 'pagos_facturacion/formulario_pago.html', {
        'formulario': formulario,
        'factura': factura,
        'titulo': 'Editar pago',
    })


@requiere_permiso('pagos')
def eliminar_pago(request, id, indice):
    factura = buscar_factura(id)
    if factura and request.method == 'POST' and factura.estado != 'anulada' and indice < len(factura.pagos):
        factura.pagos.pop(indice)
        actualizar_estado(factura)
        factura.save()
        registrar_auditoria(request, 'eliminar', 'pagos', f'Eliminó un pago de la factura {factura.numero_factura}')
    return redirect('pagos:detalle_factura', id=id)


@requiere_permiso('pagos')
def lista_pagos(request):
    medio = request.GET.get('medio', '')
    medios = dict(DetallePago.TIPOS_PAGO)
    pagos = []
    for factura in Factura.objects.exclude(estado='anulada'):
        for pago in factura.pagos:
            if not medio or pago['tipo_pago'] == medio:
                pagos.append(dict(pago, factura=factura, medio=medios[pago['tipo_pago']]))
    pagos.sort(key=lambda p: p['fecha_pago'], reverse=True)

    return render(request, 'pagos_facturacion/lista_pagos.html', {
        'pagos': pagos,
        'medio': medio,
        'medios': DetallePago.TIPOS_PAGO,
        'total': sum(p['monto'] for p in pagos),
    })
