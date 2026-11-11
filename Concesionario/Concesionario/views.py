from django.shortcuts import render

from clientes_vehiculos.models import Cliente, Vehiculo
from clientes_vehiculos.views import todas_las_cotizaciones
from gestion_usuarios.models import Usuario
from gestion_usuarios.sesion import requiere_permiso
from pagos_facturacion.models import Factura


@requiere_permiso()
def inicio(request):
    """Tablero general: reúne la información de todas las aplicaciones."""
    cotizaciones = todas_las_cotizaciones()
    ventas = [c for c in cotizaciones if c.venta]
    ventas.sort(key=lambda c: c.venta['fecha_venta'], reverse=True)
    facturas = Factura.objects.exclude(estado='anulada')
    recaudado = sum(sum(p['monto'] for p in f.pagos) for f in facturas)

    usuario = Usuario.objects.get(id=request.session['usuario']['id'])
    datos = {
        'clientes': Cliente.objects.count(),
        'vehiculos': Vehiculo.objects.count(),
        'disponibles': Vehiculo.objects.filter(estado='disponible').count(),
        'reservados': Vehiculo.objects.filter(estado='reservado').count(),
        'vendidos': Vehiculo.objects.filter(estado='vendido').count(),
        'cotizaciones_pendientes': len([c for c in cotizaciones if c.estado == 'pendiente']),
        'cantidad_ventas': len(ventas),
        'total_vendido': sum(c.venta['precio_final'] or 0 for c in ventas),
        'total_recaudado': recaudado,
        'por_cobrar': sum(f.total for f in facturas) - recaudado,
        'ultimas_ventas': ventas[:5],
        'destacados': Vehiculo.objects.filter(estado='disponible').order_by('-id')[:4],
        'no_leidas': len([n for n in usuario.notificaciones if not n['leida']]),
    }
    total = datos['vehiculos'] or 1
    datos['porcentaje_disponibles'] = round(datos['disponibles'] * 100 / total)
    datos['porcentaje_reservados'] = round(datos['reservados'] * 100 / total)
    datos['porcentaje_vendidos'] = round(datos['vendidos'] * 100 / total)
    return render(request, 'inicio.html', datos)
