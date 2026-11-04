import datetime

from django.shortcuts import redirect, render
from clientes_vehiculos.models import Cliente, Vehiculo
from pagos_facturacion.models import Factura
from .forms import (
    FormularioCotizacion, FormularioEditarVenta, FormularioEntrega, FormularioGarantia,
    FormularioPromocion, FormularioSeguimiento, FormularioVenta,
)
from .models import (
    ESTADOS_ENTREGA, ESTADOS_GARANTIA, ESTADOS_COTIZACION, RESULTADOS_SEGUIMIENTO,
    Cotizacion, Entrega, Garantia, Promocion, Seguimiento, Venta,
)


def buscar(modelo, id):
    try:
        return modelo.objects.get(id=id)
    except modelo.DoesNotExist:
        return None


def siguiente_numero(modelo, prefijo):
    ultimo = modelo.objects.order_by('-id').first()
    return f"{prefijo}-{(ultimo.id + 1) if ultimo else 1:04d}"


def calcular_descuento(datos):
    promocion = datos.get('promocion')
    return promocion.porcentaje if promocion else datos['descuento_porcentaje']


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
            vehiculo = datos['vehiculo']
            descuento = calcular_descuento(datos)
            cotizacion = Cotizacion.objects.create(
                numero=siguiente_numero(Cotizacion, 'COT'),
                cliente=datos['cliente'],
                vehiculo=vehiculo,
                vendedor=datos['vendedor'],
                promocion=datos['promocion'],
                precio_base=vehiculo.precio,
                descuento_porcentaje=descuento,
                precio_ofertado=round(vehiculo.precio * (1 - descuento / 100)),
                fecha=datos['fecha'],
                vigencia_dias=datos['vigencia_dias'],
                notas=datos['notas'],
            )
            return redirect('ventas:detalle_cotizacion', id=cotizacion.id)
    else:
        cliente = Cliente.objects.filter(documento=request.GET.get('cliente', '')).first()
        vehiculo = Vehiculo.objects.filter(placa=request.GET.get('placa', '')).first()
        formulario = FormularioCotizacion(initial={
            'fecha': datetime.date.today(),
            'cliente': cliente.id if cliente else '',
            'vehiculo': vehiculo.id if vehiculo else '',
        })

    return render(request, 'ventas_cotizaciones/formulario_cotizacion.html', {
        'formulario': formulario,
        'titulo': 'Nueva cotizacion',
    })


def detalle_cotizacion(request, id):
    cotizacion = buscar(Cotizacion, id)
    if cotizacion is None:
        return redirect('ventas:lista_cotizaciones')

    vence = cotizacion.fecha + datetime.timedelta(days=cotizacion.vigencia_dias)
    return render(request, 'ventas_cotizaciones/detalle_cotizacion.html', {
        'cotizacion': cotizacion,
        'ahorro': cotizacion.precio_base - cotizacion.precio_ofertado,
        'vence': vence,
        'vencida': vence < datetime.date.today() and cotizacion.estado == 'pendiente',
        'venta': Venta.objects.filter(cotizacion=cotizacion).exclude(estado='anulada').first(),
        'seguimientos': Seguimiento.objects.filter(cotizacion=cotizacion).order_by('-fecha', '-id'),
    })


def editar_cotizacion(request, id):
    cotizacion = buscar(Cotizacion, id)
    if cotizacion is None:
        return redirect('ventas:lista_cotizaciones')
    if cotizacion.estado == 'vendida':
        return redirect('ventas:detalle_cotizacion', id=id)

    opciones = {'vehiculo_actual': cotizacion.vehiculo_id, 'promocion_actual': cotizacion.promocion_id}
    if request.method == 'POST':
        formulario = FormularioCotizacion(request.POST, **opciones)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            vehiculo = datos['vehiculo']
            descuento = calcular_descuento(datos)
            cotizacion.cliente = datos['cliente']
            cotizacion.vehiculo = vehiculo
            cotizacion.vendedor = datos['vendedor']
            cotizacion.promocion = datos['promocion']
            cotizacion.precio_base = vehiculo.precio
            cotizacion.descuento_porcentaje = descuento
            cotizacion.precio_ofertado = round(vehiculo.precio * (1 - descuento / 100))
            cotizacion.fecha = datos['fecha']
            cotizacion.vigencia_dias = datos['vigencia_dias']
            cotizacion.notas = datos['notas']
            cotizacion.save()
            return redirect('ventas:detalle_cotizacion', id=cotizacion.id)
    else:
        formulario = FormularioCotizacion(initial={
            'cliente': cotizacion.cliente_id,
            'vehiculo': cotizacion.vehiculo_id,
            'vendedor': cotizacion.vendedor_id,
            'promocion': cotizacion.promocion_id,
            'fecha': cotizacion.fecha,
            'descuento_porcentaje': cotizacion.descuento_porcentaje,
            'vigencia_dias': cotizacion.vigencia_dias,
            'notas': cotizacion.notas,
        }, **opciones)

    return render(request, 'ventas_cotizaciones/formulario_cotizacion.html', {
        'formulario': formulario,
        'titulo': f'Editar cotizacion {cotizacion.numero}',
        'cotizacion': cotizacion,
    })


def cambiar_estado_cotizacion(request, id, estado):
    cotizacion = buscar(Cotizacion, id)
    if (request.method == 'POST' and cotizacion is not None
            and cotizacion.estado != 'vendida' and estado in ('pendiente', 'aprobada', 'rechazada')):
        Cotizacion.objects.filter(id=id).update(estado=estado)
        # Una cotización aprobada reserva el vehículo; si se rechaza, se libera
        vehiculos = Vehiculo.objects.filter(id=cotizacion.vehiculo_id).exclude(estado='vendido')
        if estado == 'aprobada':
            vehiculos.update(estado='reservado')
        elif cotizacion.estado == 'aprobada':
            vehiculos.update(estado='disponible')
    return redirect('ventas:detalle_cotizacion', id=id)


def eliminar_cotizacion(request, id):
    cotizacion = buscar(Cotizacion, id)
    if cotizacion is None:
        return redirect('ventas:lista_cotizaciones')

    bloqueado = cotizacion.estado == 'vendida'
    if request.method == 'POST' and not bloqueado:
        if cotizacion.estado == 'aprobada':
            Vehiculo.objects.filter(id=cotizacion.vehiculo_id, estado='reservado').update(estado='disponible')
        cotizacion.delete()  # sus seguimientos se eliminan con ella
        return redirect('ventas:lista_cotizaciones')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar cotizacion',
        'objeto': f"{cotizacion.numero} · {cotizacion.cliente.nombre_completo}",
        'bloqueado': bloqueado,
        'motivo': 'La cotizacion ya se convirtio en una venta.',
        'advertencia': 'Tambien se eliminaran sus seguimientos.',
        'url_cancelar': 'ventas:detalle_cotizacion',
        'id_cancelar': cotizacion.id,
    })


def liberar_vehiculo(venta):
    if venta.cotizacion_id:
        Cotizacion.objects.filter(id=venta.cotizacion_id).update(estado='aprobada')
        estado = 'reservado'
    else:
        estado = 'disponible'
    Vehiculo.objects.filter(id=venta.vehiculo_id).update(estado=estado)


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
            vehiculo = datos['vehiculo']
            if vehiculo.estado == 'vendido':
                formulario.add_error('vehiculo', 'Este vehiculo ya fue vendido.')
            else:
                venta = Venta.objects.create(
                    numero=siguiente_numero(Venta, 'VEN'),
                    cotizacion=cotizacion,
                    cliente=datos['cliente'],
                    vehiculo=vehiculo,
                    vendedor=datos['vendedor'],
                    precio_final=datos['precio_final'] or vehiculo.precio,
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
                'cliente': cotizacion.cliente_id,
                'vehiculo': cotizacion.vehiculo_id,
                'vendedor': cotizacion.vendedor_id,
                'precio_final': cotizacion.precio_ofertado,
                'observaciones': f'Venta generada desde la cotizacion {cotizacion.numero}.',
            })
        formulario = FormularioVenta(initial=inicial)

    return render(request, 'ventas_cotizaciones/formulario_venta.html', {
        'formulario': formulario,
        'titulo': f'Vender cotizacion {cotizacion.numero}' if cotizacion else 'Registrar venta',
        'cotizacion': cotizacion,
    })


def crear_venta(request):
    return registrar_venta(request)


def vender_cotizacion(request, id):
    cotizacion = buscar(Cotizacion, id)
    if cotizacion is None or cotizacion.estado in ('vendida', 'rechazada'):
        return redirect('ventas:lista_cotizaciones')
    return registrar_venta(request, cotizacion)


def detalle_venta(request, id):
    venta = buscar(Venta, id)
    if venta is None:
        return redirect('ventas:lista_ventas')

    return render(request, 'ventas_cotizaciones/detalle_venta.html', {
        'venta': venta,
        'factura': Factura.objects.filter(numero_venta=venta.numero).first(),
        'cotizacion': venta.cotizacion,
        'entregas': Entrega.objects.filter(venta=venta).order_by('-fecha_programada'),
        'garantias': Garantia.objects.filter(venta=venta).order_by('-fecha_inicio'),
    })


def editar_venta(request, id):
    venta = buscar(Venta, id)
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
    venta = buscar(Venta, id)
    if request.method == 'POST' and venta is not None and venta.estado == 'activa':
        Venta.objects.filter(id=id).update(estado='anulada')
        # El vehículo vuelve al inventario, la cotización se reabre y la factura se anula
        liberar_vehiculo(venta)
        Factura.objects.filter(numero_venta=venta.numero).update(estado='anulada')
        # Las entregas pendientes se cancelan y las garantías dejan de valer
        Entrega.objects.filter(venta=venta).exclude(estado='entregada').update(estado='cancelada')
        Garantia.objects.filter(venta=venta).update(estado='anulada')
    return redirect('ventas:detalle_venta', id=id)


def eliminar_venta(request, id):
    venta = buscar(Venta, id)
    if venta is None:
        return redirect('ventas:lista_ventas')

    bloqueado = venta.facturada
    if request.method == 'POST' and not bloqueado:
        if venta.estado == 'activa':
            liberar_vehiculo(venta)
        venta.delete()  # sus entregas y garantías se eliminan con ella
        return redirect('ventas:lista_ventas')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar venta',
        'objeto': f"{venta.numero} · {venta.cliente.nombre_completo}",
        'bloqueado': bloqueado,
        'motivo': 'La venta ya tiene factura. Primero elimina la factura o anula la venta.',
        'advertencia': 'El vehiculo volvera al inventario y se eliminaran sus entregas y garantias.',
        'url_cancelar': 'ventas:detalle_venta',
        'id_cancelar': venta.id,
    })


def lista_promociones(request):
    hoy = datetime.date.today()
    promociones = list(Promocion.objects.all().order_by('-fecha_inicio'))
    for p in promociones:
        p.vigente = p.esta_vigente(hoy)
        p.cantidad_cotizaciones = Cotizacion.objects.filter(promocion=p).count()
    return render(request, 'ventas_cotizaciones/lista_promociones.html', {
        'promociones': promociones,
        'vigentes': len([p for p in promociones if p.vigente]),
    })


def _guardar_promocion(promocion, datos):
    promocion.nombre = datos['nombre']
    promocion.descripcion = datos['descripcion']
    promocion.porcentaje = datos['porcentaje']
    promocion.fecha_inicio = datos['fecha_inicio']
    promocion.fecha_fin = datos['fecha_fin']
    promocion.activa = datos['activa']
    promocion.save()


def _nombre_repetido(datos, promocion=None):
    otros = Promocion.objects.filter(nombre=datos['nombre'])
    if promocion is not None:
        otros = otros.exclude(id=promocion.id)
    return otros.exists()


def crear_promocion(request):
    if request.method == 'POST':
        formulario = FormularioPromocion(request.POST)
        if formulario.is_valid():
            if _nombre_repetido(formulario.cleaned_data):
                formulario.add_error('nombre', 'Ya existe una promocion con ese nombre.')
            else:
                _guardar_promocion(Promocion(), formulario.cleaned_data)
                return redirect('ventas:lista_promociones')
    else:
        hoy = datetime.date.today()
        formulario = FormularioPromocion(initial={
            'fecha_inicio': hoy, 'fecha_fin': hoy + datetime.timedelta(days=30), 'activa': True,
        })
    return render(request, 'ventas_cotizaciones/formulario_promocion.html', {
        'formulario': formulario, 'titulo': 'Nueva promocion',
    })


def editar_promocion(request, id):
    promocion = buscar(Promocion, id)
    if promocion is None:
        return redirect('ventas:lista_promociones')

    if request.method == 'POST':
        formulario = FormularioPromocion(request.POST)
        if formulario.is_valid():
            if _nombre_repetido(formulario.cleaned_data, promocion):
                formulario.add_error('nombre', 'Ya existe una promocion con ese nombre.')
            else:
                _guardar_promocion(promocion, formulario.cleaned_data)
                return redirect('ventas:lista_promociones')
    else:
        formulario = FormularioPromocion(initial={
            'nombre': promocion.nombre, 'descripcion': promocion.descripcion,
            'porcentaje': promocion.porcentaje, 'fecha_inicio': promocion.fecha_inicio,
            'fecha_fin': promocion.fecha_fin, 'activa': promocion.activa,
        })
    return render(request, 'ventas_cotizaciones/formulario_promocion.html', {
        'formulario': formulario, 'titulo': f'Editar promocion {promocion.nombre}',
    })


def eliminar_promocion(request, id):
    promocion = buscar(Promocion, id)
    if promocion is None:
        return redirect('ventas:lista_promociones')

    if request.method == 'POST':
        promocion.delete()  # las cotizaciones que la usaron conservan su descuento
        return redirect('ventas:lista_promociones')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar promocion',
        'objeto': promocion.nombre,
        'advertencia': 'Las cotizaciones que usaron esta promocion conservan su descuento.',
        'url_cancelar': 'ventas:lista_promociones',
    })

def lista_seguimientos(request):
    seguimientos = Seguimiento.objects.all().order_by('-fecha', '-id')
    resultado = request.GET.get('resultado', '')
    if resultado:
        seguimientos = seguimientos.filter(resultado=resultado)
    return render(request, 'ventas_cotizaciones/lista_seguimientos.html', {
        'seguimientos': seguimientos,
        'resultado': resultado,
        'resultados': RESULTADOS_SEGUIMIENTO,
        'hoy': datetime.date.today(),
    })


def _guardar_seguimiento(seguimiento, datos):
    seguimiento.cotizacion = datos['cotizacion']
    seguimiento.fecha = datos['fecha']
    seguimiento.medio = datos['medio']
    seguimiento.resultado = datos['resultado']
    seguimiento.comentario = datos['comentario']
    seguimiento.proxima_fecha = datos['proxima_fecha']
    seguimiento.save()


def crear_seguimiento(request):
    if request.method == 'POST':
        formulario = FormularioSeguimiento(request.POST)
        if formulario.is_valid():
            seguimiento = Seguimiento()
            _guardar_seguimiento(seguimiento, formulario.cleaned_data)
            return redirect('ventas:detalle_cotizacion', id=seguimiento.cotizacion_id)
    else:
        formulario = FormularioSeguimiento(initial={
            'fecha': datetime.date.today(), 'cotizacion': request.GET.get('cotizacion', ''),
        })
    return render(request, 'ventas_cotizaciones/formulario_seguimiento.html', {
        'formulario': formulario, 'titulo': 'Nuevo seguimiento',
    })


def editar_seguimiento(request, id):
    seguimiento = buscar(Seguimiento, id)
    if seguimiento is None:
        return redirect('ventas:lista_seguimientos')

    if request.method == 'POST':
        formulario = FormularioSeguimiento(request.POST, cotizacion_actual=seguimiento.cotizacion_id)
        if formulario.is_valid():
            _guardar_seguimiento(seguimiento, formulario.cleaned_data)
            return redirect('ventas:lista_seguimientos')
    else:
        formulario = FormularioSeguimiento(cotizacion_actual=seguimiento.cotizacion_id, initial={
            'cotizacion': seguimiento.cotizacion_id, 'fecha': seguimiento.fecha, 'medio': seguimiento.medio,
            'resultado': seguimiento.resultado, 'comentario': seguimiento.comentario,
            'proxima_fecha': seguimiento.proxima_fecha,
        })
    return render(request, 'ventas_cotizaciones/formulario_seguimiento.html', {
        'formulario': formulario, 'titulo': f'Editar seguimiento de {seguimiento.cotizacion.numero}',
    })


def eliminar_seguimiento(request, id):
    seguimiento = buscar(Seguimiento, id)
    if seguimiento is None:
        return redirect('ventas:lista_seguimientos')

    if request.method == 'POST':
        seguimiento.delete()
        return redirect('ventas:lista_seguimientos')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar seguimiento',
        'objeto': f"{seguimiento.cotizacion.numero} · {seguimiento.fecha:%d/%m/%Y}",
        'url_cancelar': 'ventas:lista_seguimientos',
    })

def lista_entregas(request):
    entregas = Entrega.objects.all().order_by('-fecha_programada', '-id')
    estado = request.GET.get('estado', '')
    if estado:
        entregas = entregas.filter(estado=estado)
    return render(request, 'ventas_cotizaciones/lista_entregas.html', {
        'entregas': entregas,
        'estado': estado,
        'estados': ESTADOS_ENTREGA,
        'resumen': {e: Entrega.objects.filter(estado=e).count() for e, _ in ESTADOS_ENTREGA},
    })


def _guardar_entrega(entrega, datos):
    entrega.venta = datos['venta']
    entrega.fecha_programada = datos['fecha_programada']
    entrega.fecha_entrega = datos['fecha_entrega'] if datos['estado'] == 'entregada' else None
    entrega.lugar = datos['lugar']
    entrega.estado = datos['estado']
    entrega.observaciones = datos['observaciones']
    entrega.save()


def _venta_ya_entregada(datos, entrega=None):
    otras = Entrega.objects.filter(venta=datos['venta']).exclude(estado='cancelada')
    if entrega is not None:
        otras = otras.exclude(id=entrega.id)
    return datos['estado'] != 'cancelada' and otras.exists()


def crear_entrega(request):
    if request.method == 'POST':
        formulario = FormularioEntrega(request.POST)
        if formulario.is_valid():
            if _venta_ya_entregada(formulario.cleaned_data):
                formulario.add_error('venta', 'Esta venta ya tiene una entrega registrada.')
            else:
                entrega = Entrega()
                _guardar_entrega(entrega, formulario.cleaned_data)
                return redirect('ventas:detalle_venta', id=entrega.venta_id)
    else:
        formulario = FormularioEntrega(initial={
            'fecha_programada': datetime.date.today() + datetime.timedelta(days=3),
            'lugar': 'Sede principal del concesionario',
            'venta': request.GET.get('venta', ''),
        })
    return render(request, 'ventas_cotizaciones/formulario_entrega.html', {
        'formulario': formulario, 'titulo': 'Programar entrega',
    })


def editar_entrega(request, id):
    entrega = buscar(Entrega, id)
    if entrega is None:
        return redirect('ventas:lista_entregas')

    if request.method == 'POST':
        formulario = FormularioEntrega(request.POST, venta_actual=entrega.venta_id)
        if formulario.is_valid():
            if _venta_ya_entregada(formulario.cleaned_data, entrega):
                formulario.add_error('venta', 'Esta venta ya tiene otra entrega registrada.')
            else:
                _guardar_entrega(entrega, formulario.cleaned_data)
                return redirect('ventas:lista_entregas')
    else:
        formulario = FormularioEntrega(venta_actual=entrega.venta_id, initial={
            'venta': entrega.venta_id, 'fecha_programada': entrega.fecha_programada,
            'fecha_entrega': entrega.fecha_entrega, 'lugar': entrega.lugar,
            'estado': entrega.estado, 'observaciones': entrega.observaciones,
        })
    return render(request, 'ventas_cotizaciones/formulario_entrega.html', {
        'formulario': formulario, 'titulo': f'Editar entrega de {entrega.venta.numero}',
    })


def eliminar_entrega(request, id):
    entrega = buscar(Entrega, id)
    if entrega is None:
        return redirect('ventas:lista_entregas')

    if request.method == 'POST':
        entrega.delete()
        return redirect('ventas:lista_entregas')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar entrega',
        'objeto': f"{entrega.venta.numero} · {entrega.fecha_programada:%d/%m/%Y}",
        'url_cancelar': 'ventas:lista_entregas',
    })


def lista_garantias(request):
    garantias = Garantia.objects.all().order_by('-fecha_inicio', '-id')
    estado = request.GET.get('estado', '')
    if estado:
        garantias = garantias.filter(estado=estado)
    return render(request, 'ventas_cotizaciones/lista_garantias.html', {
        'garantias': garantias,
        'estado': estado,
        'estados': ESTADOS_GARANTIA,
        'resumen': {e: Garantia.objects.filter(estado=e).count() for e, _ in ESTADOS_GARANTIA},
    })


def _guardar_garantia(garantia, datos):
    garantia.venta = datos['venta']
    garantia.tipo = datos['tipo']
    garantia.meses = datos['meses']
    garantia.kilometraje_limite = datos['kilometraje_limite']
    garantia.fecha_inicio = datos['fecha_inicio']
    garantia.estado = datos['estado']
    garantia.cobertura = datos['cobertura']
    garantia.save()


def _inicio_antes_de_la_venta(datos):
    return datos['fecha_inicio'] < datos['venta'].fecha_venta


def crear_garantia(request):
    if request.method == 'POST':
        formulario = FormularioGarantia(request.POST)
        if formulario.is_valid():
            if _inicio_antes_de_la_venta(formulario.cleaned_data):
                formulario.add_error('fecha_inicio', 'La garantia no puede empezar antes de la venta.')
            else:
                garantia = Garantia()
                _guardar_garantia(garantia, formulario.cleaned_data)
                return redirect('ventas:detalle_venta', id=garantia.venta_id)
    else:
        formulario = FormularioGarantia(initial={
            'fecha_inicio': datetime.date.today(), 'estado': 'vigente',
            'venta': request.GET.get('venta', ''),
        })
    return render(request, 'ventas_cotizaciones/formulario_garantia.html', {
        'formulario': formulario, 'titulo': 'Nueva garantia',
    })


def editar_garantia(request, id):
    garantia = buscar(Garantia, id)
    if garantia is None:
        return redirect('ventas:lista_garantias')

    if request.method == 'POST':
        formulario = FormularioGarantia(request.POST, venta_actual=garantia.venta_id)
        if formulario.is_valid():
            if _inicio_antes_de_la_venta(formulario.cleaned_data):
                formulario.add_error('fecha_inicio', 'La garantía no puede empezar antes de la venta.')
            else:
                _guardar_garantia(garantia, formulario.cleaned_data)
                return redirect('ventas:lista_garantias')
    else:
        formulario = FormularioGarantia(venta_actual=garantia.venta_id, initial={
            'venta': garantia.venta_id, 'tipo': garantia.tipo, 'meses': garantia.meses,
            'kilometraje_limite': garantia.kilometraje_limite, 'fecha_inicio': garantia.fecha_inicio,
            'estado': garantia.estado, 'cobertura': garantia.cobertura,
        })
    return render(request, 'ventas_cotizaciones/formulario_garantia.html', {
        'formulario': formulario, 'titulo': f'Editar garantia de {garantia.venta.numero}',
    })


def eliminar_garantia(request, id):
    garantia = buscar(Garantia, id)
    if garantia is None:
        return redirect('ventas:lista_garantias')

    if request.method == 'POST':
        garantia.delete()
        return redirect('ventas:lista_garantias')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar garantia',
        'objeto': f"{garantia.get_tipo_display()} · {garantia.venta.numero}",
        'url_cancelar': 'ventas:lista_garantias',
    })
