from django.db.models import Q
from django.shortcuts import redirect, render

from gestion_usuarios.sesion import registrar_auditoria, requiere_permiso
from pagos_facturacion.models import Factura
from .forms import FormularioCliente, FormularioVehiculo
from .models import Cliente, Vehiculo


def buscar_cliente(id):
    try:
        return Cliente.objects.get(id=id)
    except Cliente.DoesNotExist:
        return None


def buscar_vehiculo(id):
    try:
        return Vehiculo.objects.get(id=id)
    except Vehiculo.DoesNotExist:
        return None


def todas_las_cotizaciones():
    """Recorre las cotizaciones embebidas en todos los clientes.
    Cada elemento trae el cliente y la posición de la cotización en su arreglo."""
    lista = []
    for cliente in Cliente.objects.all():
        for indice, cotizacion in enumerate(cliente.cotizaciones):
            lista.append(dict(cotizacion, cliente=cliente, indice=indice))
    return lista


def actualizar_estado_vehiculo(placa):
    """El estado del vehículo depende de sus cotizaciones:
    vendido si tiene una venta, reservado si tiene una cotización aprobada."""
    cotizaciones = [c for c in todas_las_cotizaciones() if c['vehiculo']['placa'] == placa]
    if any(c['venta'] for c in cotizaciones):
        estado = 'vendido'
    elif any(c['estado'] == 'aprobada' for c in cotizaciones):
        estado = 'reservado'
    else:
        estado = 'disponible'
    Vehiculo.objects.filter(placa=placa).update(estado=estado)


# ---------------- Clientes ----------------

@requiere_permiso('clientes')
def lista_clientes(request):
    clientes = Cliente.objects.all().order_by('-id')
    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        clientes = clientes.filter(
            Q(nombre__icontains=busqueda) | Q(apellido__icontains=busqueda) |
            Q(cedula__icontains=busqueda) | Q(email__icontains=busqueda)
        )
    return render(request, 'clientes_vehiculos/lista_clientes.html', {
        'clientes': clientes,
        'busqueda': busqueda,
        'total': Cliente.objects.count(),
    })


@requiere_permiso('clientes')
def crear_cliente(request):
    if request.method == 'POST':
        formulario = FormularioCliente(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            cliente = Cliente.objects.create(
                nombre=datos['nombre'],
                apellido=datos['apellido'],
                cedula=datos['cedula'],
                email=datos['email'],
                telefono=datos['telefono'],
                direccion=datos['direccion'],
                cotizaciones=[],
            )
            registrar_auditoria(request, 'crear', 'clientes', f'Registró al cliente {cliente.cedula}')
            return redirect('clientes:detalle_cliente', id=cliente.id)
    else:
        formulario = FormularioCliente()

    return render(request, 'clientes_vehiculos/formulario_cliente.html', {
        'formulario': formulario,
        'titulo': 'Nuevo cliente',
    })


@requiere_permiso('clientes')
def detalle_cliente(request, id):
    cliente = buscar_cliente(id)
    if cliente is None:
        return redirect('clientes:lista_clientes')

    cotizaciones = [dict(c, indice=i) for i, c in enumerate(cliente.cotizaciones)]
    compras = [c for c in cotizaciones if c['venta']]
    return render(request, 'clientes_vehiculos/detalle_cliente.html', {
        'cliente': cliente,
        'cotizaciones': cotizaciones,
        'compras': compras,
        'total_compras': sum(c['venta']['precio_final'] or 0 for c in compras),
        'facturas': Factura.objects.filter(cedula_cliente=cliente.cedula).order_by('-id'),
    })


@requiere_permiso('clientes')
def editar_cliente(request, id):
    cliente = buscar_cliente(id)
    if cliente is None:
        return redirect('clientes:lista_clientes')

    if request.method == 'POST':
        formulario = FormularioCliente(request.POST, editando=True, initial={'cedula': cliente.cedula})
        if formulario.is_valid():
            datos = formulario.cleaned_data
            cliente.nombre = datos['nombre']
            cliente.apellido = datos['apellido']
            cliente.telefono = datos['telefono']
            cliente.email = datos['email']
            cliente.direccion = datos['direccion']
            cliente.save()
            registrar_auditoria(request, 'editar', 'clientes', f'Editó al cliente {cliente.cedula}')
            return redirect('clientes:detalle_cliente', id=cliente.id)
    else:
        formulario = FormularioCliente(editando=True, initial={
            'cedula': cliente.cedula,
            'nombre': cliente.nombre,
            'apellido': cliente.apellido,
            'telefono': cliente.telefono,
            'email': cliente.email,
            'direccion': cliente.direccion,
        })

    return render(request, 'clientes_vehiculos/formulario_cliente.html', {
        'formulario': formulario,
        'titulo': f'Editar cliente {cliente.nombre} {cliente.apellido}',
        'cliente': cliente,
    })


@requiere_permiso('clientes')
def eliminar_cliente(request, id):
    cliente = buscar_cliente(id)
    if cliente is None:
        return redirect('clientes:lista_clientes')

    con_ventas = any(c['venta'] for c in cliente.cotizaciones)
    if request.method == 'POST' and not con_ventas:
        placas = [c['vehiculo']['placa'] for c in cliente.cotizaciones]
        cliente.delete()
        for placa in placas:
            actualizar_estado_vehiculo(placa)
        registrar_auditoria(request, 'eliminar', 'clientes', f'Eliminó al cliente {cliente.cedula}')
        return redirect('clientes:lista_clientes')

    cantidad = len(cliente.cotizaciones)
    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar cliente',
        'objeto': f'{cliente.nombre} {cliente.apellido} (C.C. {cliente.cedula})',
        'bloqueado': con_ventas,
        'motivo': 'El cliente tiene ventas registradas. Primero elimina esas ventas.',
        'advertencia': f'También se eliminarán sus {cantidad} cotizaciones.' if cantidad else '',
        'url_cancelar': 'clientes:detalle_cliente',
        'id_cancelar': cliente.id,
    })


# ---------------- Vehículos ----------------

@requiere_permiso('clientes')
def catalogo_vehiculos(request):
    vehiculos = Vehiculo.objects.all().order_by('-id')
    busqueda = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '')
    if busqueda:
        vehiculos = vehiculos.filter(
            Q(marca__icontains=busqueda) | Q(modelo__icontains=busqueda) | Q(placa__icontains=busqueda)
        )
    if estado:
        vehiculos = vehiculos.filter(estado=estado)

    return render(request, 'clientes_vehiculos/catalogo_vehiculos.html', {
        'vehiculos': vehiculos,
        'busqueda': busqueda,
        'estado': estado,
        'estados': Vehiculo.ESTADOS,
        'total': Vehiculo.objects.count(),
    })


@requiere_permiso('clientes')
def crear_vehiculo(request):
    if request.method == 'POST':
        formulario = FormularioVehiculo(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            vehiculo = Vehiculo.objects.create(
                marca=datos['marca'],
                modelo=datos['modelo'],
                anio=datos['anio'],
                color=datos['color'],
                placa=datos['placa'],
                precio=datos['precio'],
                kilometraje=datos['kilometraje'],
                estado=datos['estado'],
                descripcion=datos['descripcion'],
                propietarios_anteriores=[],
                mantenimientos=[],
            )
            registrar_auditoria(request, 'crear', 'vehiculos', f'Registró el vehículo {vehiculo.placa}')
            return redirect('clientes:detalle_vehiculo', id=vehiculo.id)
    else:
        formulario = FormularioVehiculo()

    return render(request, 'clientes_vehiculos/formulario_vehiculo.html', {
        'formulario': formulario,
        'titulo': 'Nuevo vehículo',
    })


@requiere_permiso('clientes')
def detalle_vehiculo(request, id):
    vehiculo = buscar_vehiculo(id)
    if vehiculo is None:
        return redirect('clientes:catalogo_vehiculos')

    cotizaciones = [c for c in todas_las_cotizaciones() if c['vehiculo']['placa'] == vehiculo.placa]
    return render(request, 'clientes_vehiculos/detalle_vehiculo.html', {
        'vehiculo': vehiculo,
        'cotizaciones': cotizaciones,
        'costo_mantenimientos': sum(m['costo'] or 0 for m in vehiculo.mantenimientos),
    })


@requiere_permiso('clientes')
def editar_vehiculo(request, id):
    vehiculo = buscar_vehiculo(id)
    if vehiculo is None:
        return redirect('clientes:catalogo_vehiculos')

    if request.method == 'POST':
        formulario = FormularioVehiculo(request.POST, editando=True, initial={'placa': vehiculo.placa})
        if formulario.is_valid():
            datos = formulario.cleaned_data
            vehiculo.marca = datos['marca']
            vehiculo.modelo = datos['modelo']
            vehiculo.anio = datos['anio']
            vehiculo.color = datos['color']
            vehiculo.precio = datos['precio']
            vehiculo.kilometraje = datos['kilometraje']
            vehiculo.estado = datos['estado']
            vehiculo.descripcion = datos['descripcion']
            vehiculo.save()
            registrar_auditoria(request, 'editar', 'vehiculos', f'Editó el vehículo {vehiculo.placa}')
            return redirect('clientes:detalle_vehiculo', id=vehiculo.id)
    else:
        formulario = FormularioVehiculo(editando=True, initial={
            'placa': vehiculo.placa,
            'marca': vehiculo.marca,
            'modelo': vehiculo.modelo,
            'anio': vehiculo.anio,
            'color': vehiculo.color,
            'precio': vehiculo.precio,
            'kilometraje': vehiculo.kilometraje,
            'estado': vehiculo.estado,
            'descripcion': vehiculo.descripcion,
        })

    return render(request, 'clientes_vehiculos/formulario_vehiculo.html', {
        'formulario': formulario,
        'titulo': f'Editar {vehiculo.marca} {vehiculo.modelo}',
        'vehiculo': vehiculo,
    })


@requiere_permiso('clientes')
def eliminar_vehiculo(request, id):
    vehiculo = buscar_vehiculo(id)
    if vehiculo is None:
        return redirect('clientes:catalogo_vehiculos')

    cotizado = any(c['vehiculo']['placa'] == vehiculo.placa for c in todas_las_cotizaciones())
    if request.method == 'POST' and not cotizado:
        vehiculo.delete()
        registrar_auditoria(request, 'eliminar', 'vehiculos', f'Eliminó el vehículo {vehiculo.placa}')
        return redirect('clientes:catalogo_vehiculos')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar vehículo',
        'objeto': f'{vehiculo.marca} {vehiculo.modelo} ({vehiculo.placa})',
        'bloqueado': cotizado,
        'motivo': 'El vehículo aparece en cotizaciones de clientes. Primero elimina esas cotizaciones.',
        'advertencia': 'También se borrará su historial de propietarios y mantenimientos.',
        'url_cancelar': 'clientes:detalle_vehiculo',
        'id_cancelar': vehiculo.id,
    })
