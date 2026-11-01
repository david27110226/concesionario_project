import datetime

from django.shortcuts import redirect, render

from clientes_vehiculos.models import Cliente, Vehiculo
from gestion_usuarios.models import Usuario
from pagos_facturacion.models import Factura
from .forms import FormularioCotizacion, FormularioEditarVenta, FormularioVenta
from .models import ESTADOS_COTIZACION, Cotizacion, Venta


def buscar_cotizacion(id):
    try:
        return Cotizacion.objects.get(id=id)
    except Cotizacion.DoesNotExist:
        return None


def buscar_venta(id):
    try:
        return Venta.objects.get(id=id)
    except Venta.DoesNotExist:
        return None


def siguiente_numero(modelo, prefijo):
    ultimo = modelo.objects.order_by('-id').first()
    return f"{prefijo}-{(ultimo.id + 1) if ultimo else 1:04d}"


def cargar_seleccion(datos, formulario):
    """Busca en sus colecciones el cliente, vehículo y asesor elegidos en el formulario."""
    cliente = Cliente.objects.filter(documento=datos['cliente']).first()
    vehiculo = Vehiculo.objects.filter(placa=datos['vehiculo']).first()
    vendedor = Usuario.objects.filter(nombre_usuario=datos['vendedor']).first()
    if cliente is None:
        formulario.add_error('cliente', 'El cliente no existe.')
    if vehiculo is None:
        formulario.add_error('vehiculo', 'El vehículo no existe.')
    if vendedor is None:
        formulario.add_error('vendedor', 'El asesor no existe.')
    return cliente, vehiculo, vendedor


# ---------------- Cotizaciones ----------------

def lista_cotizaciones(request):
    cotizaciones = Cotizacion.objects.all().order_by('-id')
    estado = request.GET.get('estado', '')
    if estado:
        cotizaciones = cotizaciones.filter(estado=estado)

    resumen = {e: Cotizacion.objects.filter(estado=e).count() for e, _ in ESTADOS_COTIZACION}
    return render(request, 'ventas_cotizaciones/lista_cotizaciones.html', {
        'cotizaciones': cotizaciones,
        'estado': estado,
        'estados': ESTADOS_COTIZACION,
        'resumen': resumen,
    })


def crear_cotizacion(request):
    if request.method == 'POST':
        formulario = FormularioCotizacion(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            cliente, vehiculo, vendedor = cargar_seleccion(datos, formulario)
            if formulario.is_valid():
                descuento = datos['descuento_porcentaje']
                cotizacion = Cotizacion.objects.create(
                    numero=siguiente_numero(Cotizacion, 'COT'),
                    cliente=cliente.resumen(),
                    vehiculo=vehiculo.resumen(),
                    vendedor=vendedor.resumen(),
                    precio_base=vehiculo.precio,
                    descuento_porcentaje=descuento,
                    precio_ofertado=round(vehiculo.precio * (1 - descuento / 100)),
                    fecha=datos['fecha'],
                    vigencia_dias=datos['vigencia_dias'],
                    notas=datos['notas'],
                )
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


def detalle_cotizacion(request, id):
    cotizacion = buscar_cotizacion(id)
    if cotizacion is None:
        return redirect('ventas:lista_cotizaciones')

    vence = cotizacion.fecha + datetime.timedelta(days=cotizacion.vigencia_dias)
    return render(request, 'ventas_cotizaciones/detalle_cotizacion.html', {
        'cotizacion': cotizacion,
        'ahorro': cotizacion.precio_base - cotizacion.precio_ofertado,
        'vence': vence,
        'vencida': vence < datetime.date.today() and cotizacion.estado == 'pendiente',
        'venta': Venta.objects.filter(numero_cotizacion=cotizacion.numero).first(),
        'cliente': Cliente.objects.filter(documento=cotizacion.cliente['documento']).first(),
        'vehiculo': Vehiculo.objects.filter(placa=cotizacion.vehiculo['placa']).first(),
    })


def editar_cotizacion(request, id):
    cotizacion = buscar_cotizacion(id)
    if cotizacion is None:
        return redirect('ventas:lista_cotizaciones')
    if cotizacion.estado == 'vendida':
        return redirect('ventas:detalle_cotizacion', id=id)

    placa = cotizacion.vehiculo['placa']
    if request.method == 'POST':
        formulario = FormularioCotizacion(request.POST, placa_actual=placa)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            cliente, vehiculo, vendedor = cargar_seleccion(datos, formulario)
            if formulario.is_valid():
                descuento = datos['descuento_porcentaje']
                cotizacion.cliente = cliente.resumen()
                cotizacion.vehiculo = vehiculo.resumen()
                cotizacion.vendedor = vendedor.resumen()
                cotizacion.precio_base = vehiculo.precio
                cotizacion.descuento_porcentaje = descuento
                cotizacion.precio_ofertado = round(vehiculo.precio * (1 - descuento / 100))
                cotizacion.fecha = datos['fecha']
                cotizacion.vigencia_dias = datos['vigencia_dias']
                cotizacion.notas = datos['notas']
                cotizacion.save()
                return redirect('ventas:detalle_cotizacion', id=cotizacion.id)
    else:
        formulario = FormularioCotizacion(placa_actual=placa, initial={
            'cliente': cotizacion.cliente['documento'],
            'vehiculo': placa,
            'vendedor': cotizacion.vendedor['nombre_usuario'],
            'fecha': cotizacion.fecha,
            'descuento_porcentaje': cotizacion.descuento_porcentaje,
            'vigencia_dias': cotizacion.vigencia_dias,
            'notas': cotizacion.notas,
        })

    return render(request, 'ventas_cotizaciones/formulario_cotizacion.html', {
        'formulario': formulario,
        'titulo': f'Editar cotización {cotizacion.numero}',
        'cotizacion': cotizacion,
    })


def cambiar_estado_cotizacion(request, id, estado):
    cotizacion = buscar_cotizacion(id)
    if (request.method == 'POST' and cotizacion is not None
            and cotizacion.estado != 'vendida' and estado in ('pendiente', 'aprobada', 'rechazada')):
        Cotizacion.objects.filter(id=id).update(estado=estado)
        # Una cotización aprobada reserva el vehículo; si se rechaza, se libera
        vehiculos = Vehiculo.objects.filter(placa=cotizacion.vehiculo['placa']).exclude(estado='vendido')
        if estado == 'aprobada':
            vehiculos.update(estado='reservado')
        elif cotizacion.estado == 'aprobada':
            vehiculos.update(estado='disponible')
    return redirect('ventas:detalle_cotizacion', id=id)


def eliminar_cotizacion(request, id):
    cotizacion = buscar_cotizacion(id)
    if cotizacion is None:
        return redirect('ventas:lista_cotizaciones')

    bloqueado = cotizacion.estado == 'vendida'
    if request.method == 'POST' and not bloqueado:
        if cotizacion.estado == 'aprobada':
            Vehiculo.objects.filter(placa=cotizacion.vehiculo['placa'], estado='reservado').update(estado='disponible')
        cotizacion.delete()
        return redirect('ventas:lista_cotizaciones')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar cotización',
        'objeto': f"{cotizacion.numero} · {cotizacion.cliente['nombre_completo']}",
        'bloqueado': bloqueado,
        'motivo': 'La cotización ya se convirtió en una venta.',
        'url_cancelar': 'ventas:detalle_cotizacion',
        'id_cancelar': cotizacion.id,
    })


# ---------------- Ventas ----------------

def liberar_vehiculo(venta):
    """Deshace los efectos de una venta: si venía de una cotización, esta vuelve a
    quedar aprobada y el vehículo reservado; si no, el vehículo queda disponible."""
    if venta.numero_cotizacion:
        Cotizacion.objects.filter(numero=venta.numero_cotizacion).update(estado='aprobada')
        estado = 'reservado'
    else:
        estado = 'disponible'
    Vehiculo.objects.filter(placa=venta.vehiculo['placa']).update(estado=estado)


def lista_ventas(request):
    ventas = Venta.objects.all().order_by('-id')
    estado = request.GET.get('estado', '')
    if estado:
        ventas = ventas.filter(estado=estado)

    activas = Venta.objects.filter(estado='activa')
    return render(request, 'ventas_cotizaciones/lista_ventas.html', {
        'ventas': ventas,
        'estado': estado,
        'cantidad_activas': activas.count(),
        'total_vendido': sum(v.precio_final for v in activas),
        'por_facturar': len([v for v in activas if not v.facturada]),
    })


def registrar_venta(request, cotizacion=None):
    if request.method == 'POST':
        formulario = FormularioVenta(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            cliente, vehiculo, vendedor = cargar_seleccion(datos, formulario)
            if vehiculo is not None and vehiculo.estado == 'vendido':
                formulario.add_error('vehiculo', 'Este vehículo ya fue vendido.')
            if formulario.is_valid():
                precio = datos['precio_final'] or vehiculo.precio
                venta = Venta.objects.create(
                    numero=siguiente_numero(Venta, 'VEN'),
                    numero_cotizacion=cotizacion.numero if cotizacion else '',
                    cliente=cliente.resumen(),
                    vehiculo=vehiculo.resumen(),
                    vendedor=vendedor.resumen(),
                    precio_final=precio,
                    forma_pago=datos['forma_pago'],
                    fecha_venta=datos['fecha_venta'],
                    observaciones=datos['observaciones'],
                )
                # El vehículo queda vendido y la cotización cerrada
                Vehiculo.objects.filter(id=vehiculo.id).update(estado='vendido')
                if cotizacion:
                    Cotizacion.objects.filter(id=cotizacion.id).update(estado='vendida')
                return redirect('ventas:detalle_venta', id=venta.id)
    else:
        inicial = {'fecha_venta': datetime.date.today()}
        if cotizacion:
            inicial.update({
                'cliente': cotizacion.cliente['documento'],
                'vehiculo': cotizacion.vehiculo['placa'],
                'vendedor': cotizacion.vendedor['nombre_usuario'],
                'precio_final': cotizacion.precio_ofertado,
                'observaciones': f'Venta generada desde la cotización {cotizacion.numero}.',
            })
        formulario = FormularioVenta(initial=inicial)

    return render(request, 'ventas_cotizaciones/formulario_venta.html', {
        'formulario': formulario,
        'titulo': f'Vender cotización {cotizacion.numero}' if cotizacion else 'Registrar venta',
        'cotizacion': cotizacion,
    })


def crear_venta(request):
    return registrar_venta(request)


def vender_cotizacion(request, id):
    cotizacion = buscar_cotizacion(id)
    if cotizacion is None or cotizacion.estado in ('vendida', 'rechazada'):
        return redirect('ventas:lista_cotizaciones')
    return registrar_venta(request, cotizacion)


def detalle_venta(request, id):
    venta = buscar_venta(id)
    if venta is None:
        return redirect('ventas:lista_ventas')

    return render(request, 'ventas_cotizaciones/detalle_venta.html', {
        'venta': venta,
        'factura': Factura.objects.filter(numero_venta=venta.numero).first(),
        'cliente': Cliente.objects.filter(documento=venta.cliente['documento']).first(),
        'vehiculo': Vehiculo.objects.filter(placa=venta.vehiculo['placa']).first(),
        'cotizacion': Cotizacion.objects.filter(numero=venta.numero_cotizacion).first()
        if venta.numero_cotizacion else None,
    })


def editar_venta(request, id):
    venta = buscar_venta(id)
    if venta is None or venta.estado == 'anulada':
        return redirect('ventas:lista_ventas')

    if request.method == 'POST':
        formulario = FormularioEditarVenta(request.POST, facturada=venta.facturada,
                                           initial={'precio_final': venta.precio_final})
        if formulario.is_valid():
            datos = formulario.cleaned_data
            venta.precio_final = datos['precio_final']
            venta.forma_pago = datos['forma_pago']
            venta.fecha_venta = datos['fecha_venta']
            venta.observaciones = datos['observaciones']
            venta.save()
            return redirect('ventas:detalle_venta', id=venta.id)
    else:
        formulario = FormularioEditarVenta(facturada=venta.facturada, initial={
            'precio_final': venta.precio_final,
            'forma_pago': venta.forma_pago,
            'fecha_venta': venta.fecha_venta,
            'observaciones': venta.observaciones,
        })

    return render(request, 'ventas_cotizaciones/formulario_venta.html', {
        'formulario': formulario,
        'titulo': f'Editar venta {venta.numero}',
        'venta': venta,
    })


def anular_venta(request, id):
    venta = buscar_venta(id)
    if request.method == 'POST' and venta is not None and venta.estado == 'activa':
        Venta.objects.filter(id=id).update(estado='anulada')
        # El vehículo vuelve al inventario, la cotización se reabre y la factura se anula
        liberar_vehiculo(venta)
        Factura.objects.filter(numero_venta=venta.numero).update(estado='anulada')
    return redirect('ventas:detalle_venta', id=id)


def eliminar_venta(request, id):
    venta = buscar_venta(id)
    if venta is None:
        return redirect('ventas:lista_ventas')

    bloqueado = venta.facturada
    if request.method == 'POST' and not bloqueado:
        if venta.estado == 'activa':
            liberar_vehiculo(venta)
        venta.delete()
        return redirect('ventas:lista_ventas')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar venta',
        'objeto': f"{venta.numero} · {venta.cliente['nombre_completo']}",
        'bloqueado': bloqueado,
        'motivo': 'La venta ya tiene factura. Primero elimina la factura o anula la venta.',
        'advertencia': 'El vehículo volverá al inventario.',
        'url_cancelar': 'ventas:detalle_venta',
        'id_cancelar': venta.id,
    })
