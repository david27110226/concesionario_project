from django.shortcuts import render

from clientes_vehiculos.models import Cliente, Vehiculo
from gestion_usuarios.models import Usuario
from historial_vehiculo.models import HistorialVehiculo
from pagos_facturacion.models import Factura
from ventas_cotizaciones.models import Cotizacion, Venta


def inicio(request):
    """Tablero general: reúne la información de todas las aplicaciones."""
    ventas_activas = Venta.objects.filter(estado='activa')
    facturas = Factura.objects.exclude(estado='anulada')

    datos = {
        'clientes': Cliente.objects.count(),
        'vehiculos': Vehiculo.objects.count(),
        'disponibles': Vehiculo.objects.filter(estado='disponible').count(),
        'reservados': Vehiculo.objects.filter(estado='reservado').count(),
        'vendidos': Vehiculo.objects.filter(estado='vendido').count(),
        'usuarios': Usuario.objects.count(),
        'historiales': HistorialVehiculo.objects.count(),
        'cotizaciones_pendientes': Cotizacion.objects.filter(estado='pendiente').count(),
        'cantidad_ventas': ventas_activas.count(),
        'total_vendido': sum(v.precio_final for v in ventas_activas),
        'total_recaudado': sum(f.total_pagado() for f in facturas),
        'por_cobrar': sum(f.saldo() for f in facturas),
        'ultimas_ventas': Venta.objects.all().order_by('-id')[:5],
        'ultimas_cotizaciones': Cotizacion.objects.all().order_by('-id')[:5],
        'destacados': Vehiculo.objects.filter(estado='disponible').order_by('-id')[:4],
    }
    total = datos['vehiculos'] or 1
    datos['porcentaje_disponibles'] = round(datos['disponibles'] * 100 / total)
    datos['porcentaje_reservados'] = round(datos['reservados'] * 100 / total)
    datos['porcentaje_vendidos'] = round(datos['vendidos'] * 100 / total)
    return render(request, 'inicio.html', datos)
