import datetime

from django.shortcuts import redirect, render

from ventas_cotizaciones.models import Venta
from .forms import FormularioEditarFactura, FormularioFactura, FormularioPago
from .models import ESTADOS_FACTURA, FORMAS_PAGO, TIPOS_PAGO, Factura


def buscar_factura(id):
    try:
        return Factura.objects.get(id=id)
    except Factura.DoesNotExist:
        return None


def calcular_valores(total, iva_porcentaje):
    """El precio de venta ya incluye IVA: se separa el subtotal y el impuesto."""
    subtotal = round(total / (1 + iva_porcentaje / 100), 2)
    return subtotal, round(total - subtotal, 2)


def actualizar_estado(factura):
    if factura.estado != 'anulada':
        factura.estado = 'pagada' if factura.saldo() < 1 else 'pendiente'


# ---------------- Facturas ----------------

def lista_facturas(request):
    facturas = Factura.objects.all().order_by('-id')
    estado = request.GET.get('estado', '')
    if estado:
        facturas = facturas.filter(estado=estado)

    vigentes = Factura.objects.exclude(estado='anulada')
    return render(request, 'pagos_facturacion/lista_facturas.html', {
        'facturas': facturas,
        'estado': estado,
        'estados': ESTADOS_FACTURA,
        'total_facturado': sum(f.total for f in vigentes),
        'total_recaudado': sum(f.total_pagado() for f in vigentes),
        'por_cobrar': sum(f.saldo() for f in vigentes),
        'pendientes': Factura.objects.filter(estado='pendiente').count(),
    })


def crear_factura(request):
    if request.method == 'POST':
        formulario = FormularioFactura(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            venta = Venta.objects.filter(numero=datos['venta']).first()
            if venta is None or venta.facturada:
                formulario.add_error('venta', 'La venta no existe o ya fue facturada.')
            else:
                ultimo = Factura.objects.order_by('-id').first()
                subtotal, iva = calcular_valores(venta.precio_final, datos['iva_porcentaje'])
                factura = Factura.objects.create(
                    numero_factura=f"FAC-{(ultimo.id + 1) if ultimo else 1:04d}",
                    numero_venta=venta.numero,
                    fecha_emision=datos['fecha_emision'],
                    fecha_vencimiento=datos['fecha_vencimiento'],
                    cliente=venta.cliente,
                    vehiculo=venta.vehiculo,
                    subtotal=subtotal,
                    iva_porcentaje=datos['iva_porcentaje'],
                    impuesto_iva=iva,
                    total=venta.precio_final,
                    pagos=[],
                )
                Venta.objects.filter(id=venta.id).update(facturada=True)
                return redirect('pagos:detalle_factura', id=factura.id)
    else:
        hoy = datetime.date.today()
        formulario = FormularioFactura(initial={
            'venta': request.GET.get('venta', ''),
            'fecha_emision': hoy,
            'fecha_vencimiento': hoy + datetime.timedelta(days=30),
        })

    return render(request, 'pagos_facturacion/formulario_factura.html', {
        'formulario': formulario,
        'titulo': 'Generar factura',
    })


def detalle_factura(request, id):
    factura = buscar_factura(id)
    if factura is None:
        return redirect('pagos:lista_facturas')

    tipos, formas = dict(TIPOS_PAGO), dict(FORMAS_PAGO)
    pagos = [
        dict(p, indice=i, nombre_tipo=tipos.get(p['tipo_pago']), nombre_forma=formas.get(p['forma_pago']))
        for i, p in enumerate(factura.pagos)
    ]
    return render(request, 'pagos_facturacion/detalle_factura.html', {
        'factura': factura,
        'pagos': pagos,
        'venta': Venta.objects.filter(numero=factura.numero_venta).first(),
        'vencida': factura.estado == 'pendiente' and factura.fecha_vencimiento < datetime.date.today(),
    })


def editar_factura(request, id):
    factura = buscar_factura(id)
    if factura is None or factura.estado == 'anulada':
        return redirect('pagos:lista_facturas')

    if request.method == 'POST':
        formulario = FormularioEditarFactura(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            factura.fecha_emision = datos['fecha_emision']
            factura.fecha_vencimiento = datos['fecha_vencimiento']
            factura.iva_porcentaje = datos['iva_porcentaje']
            factura.subtotal, factura.impuesto_iva = calcular_valores(factura.total, datos['iva_porcentaje'])
            factura.save()
            return redirect('pagos:detalle_factura', id=factura.id)
    else:
        formulario = FormularioEditarFactura(initial={
            'fecha_emision': factura.fecha_emision,
            'fecha_vencimiento': factura.fecha_vencimiento,
            'iva_porcentaje': factura.iva_porcentaje,
        })

    return render(request, 'pagos_facturacion/formulario_factura.html', {
        'formulario': formulario,
        'titulo': f'Editar factura {factura.numero_factura}',
        'factura': factura,
    })


def anular_factura(request, id):
    factura = buscar_factura(id)
    if request.method == 'POST' and factura is not None:
        Factura.objects.filter(id=id).update(estado='anulada')
    return redirect('pagos:detalle_factura', id=id)


def eliminar_factura(request, id):
    factura = buscar_factura(id)
    if factura is None:
        return redirect('pagos:lista_facturas')

    bloqueado = len(factura.pagos) > 0
    if request.method == 'POST' and not bloqueado:
        # La venta vuelve a quedar disponible para facturar
        Venta.objects.filter(numero=factura.numero_venta).update(facturada=False)
        factura.delete()
        return redirect('pagos:lista_facturas')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar factura',
        'objeto': f"{factura.numero_factura} · {factura.cliente['nombre_completo']}",
        'bloqueado': bloqueado,
        'motivo': 'La factura ya tiene pagos registrados. Puedes anularla en su lugar.',
        'advertencia': f'La venta {factura.numero_venta} quedará pendiente por facturar.',
        'url_cancelar': 'pagos:detalle_factura',
        'id_cancelar': factura.id,
    })


# ---------------- Pagos (embebidos dentro de la factura) ----------------

def registrar_pago(request, id):
    factura = buscar_factura(id)
    if factura is None:
        return redirect('pagos:lista_facturas')
    if factura.estado != 'pendiente':
        return redirect('pagos:detalle_factura', id=id)

    if request.method == 'POST':
        formulario = FormularioPago(request.POST, saldo=factura.saldo())
        if formulario.is_valid():
            datos = formulario.cleaned_data
            factura.pagos.append({
                'tipo_pago': datos['tipo_pago'],
                'forma_pago': datos['forma_pago'],
                'monto': datos['monto'],
                'fecha_pago': datos['fecha_pago'],
                'numero_referencia': datos['numero_referencia'],
                'observaciones': datos['observaciones'],
            })
            actualizar_estado(factura)
            factura.save()
            return redirect('pagos:detalle_factura', id=factura.id)
    else:
        formulario = FormularioPago(saldo=factura.saldo(), initial={
            'monto': factura.saldo(),
            'fecha_pago': datetime.date.today(),
            'forma_pago': 'contado' if not factura.pagos else 'cuota',
        })

    return render(request, 'pagos_facturacion/formulario_pago.html', {
        'formulario': formulario,
        'titulo': f'Registrar pago · {factura.numero_factura}',
        'factura': factura,
    })


def eliminar_pago(request, id, indice):
    factura = buscar_factura(id)
    if (factura is not None and request.method == 'POST' and factura.estado != 'anulada'
            and 0 <= indice < len(factura.pagos)):
        factura.pagos.pop(indice)
        actualizar_estado(factura)
        factura.save()
    return redirect('pagos:detalle_factura', id=id)


def lista_pagos(request):
    tipos = dict(TIPOS_PAGO)
    pagos = []
    for factura in Factura.objects.exclude(estado='anulada'):
        for pago in factura.pagos:
            pagos.append(dict(pago, factura=factura, nombre_tipo=tipos.get(pago['tipo_pago'])))
    pagos.sort(key=lambda p: p['fecha_pago'], reverse=True)

    medio = request.GET.get('medio', '')
    if medio:
        pagos = [p for p in pagos if p['tipo_pago'] == medio]

    por_medio = []
    total = sum(p['monto'] for p in pagos)
    for clave, nombre in TIPOS_PAGO:
        monto = sum(p['monto'] for p in pagos if p['tipo_pago'] == clave)
        if monto:
            por_medio.append({'nombre': nombre, 'monto': monto,
                              'porcentaje': round(monto * 100 / total) if total else 0})

    return render(request, 'pagos_facturacion/lista_pagos.html', {
        'pagos': pagos,
        'total': total,
        'por_medio': por_medio,
        'medio': medio,
        'medios': TIPOS_PAGO,
    })
