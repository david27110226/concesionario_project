from django.db.models import Q
from django.shortcuts import redirect, render

from historial_vehiculo.models import HistorialVehiculo
from pagos_facturacion.models import Factura
from ventas_cotizaciones.models import Cotizacion, Venta
from .forms import FormularioCliente, FormularioVehiculo
from .models import ESTADOS_VEHICULO, TIPOS_VEHICULO, Cliente, Vehiculo


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


def direccion_desde(datos):
    if not datos['calle']:
        return None
    return {'ciudad': datos['ciudad'], 'barrio': datos['barrio'], 'calle': datos['calle']}


def ficha_desde(datos):
    return {
        'motor': datos['motor'],
        'cilindraje': datos['cilindraje'],
        'transmision': datos['transmision'],
        'combustible': datos['combustible'],
        'puertas': datos['puertas'],
    }


# ---------------- Clientes ----------------

def lista_clientes(request):
    clientes = Cliente.objects.all().order_by('-id')
    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        clientes = clientes.filter(
            Q(nombre__icontains=busqueda) | Q(apellido__icontains=busqueda) |
            Q(documento__icontains=busqueda) | Q(email__icontains=busqueda)
        )
    return render(request, 'clientes_vehiculos/lista_clientes.html', {
        'clientes': clientes,
        'busqueda': busqueda,
        'total': Cliente.objects.count(),
    })


def crear_cliente(request):
    if request.method == 'POST':
        formulario = FormularioCliente(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            if Cliente.objects.filter(documento=datos['documento']).exists():
                formulario.add_error('documento', 'Ya existe un cliente con ese documento.')
            else:
                cliente = Cliente.objects.create(
                    tipo_documento=datos['tipo_documento'],
                    documento=datos['documento'],
                    nombre=datos['nombre'],
                    apellido=datos['apellido'],
                    email=datos['email'],
                    telefono=datos['telefono'],
                    fecha_nacimiento=datos['fecha_nacimiento'],
                    direccion=direccion_desde(datos),
                )
                return redirect('clientes:detalle_cliente', id=cliente.id)
    else:
        formulario = FormularioCliente()

    return render(request, 'clientes_vehiculos/formulario_cliente.html', {
        'formulario': formulario,
        'titulo': 'Nuevo cliente',
    })


def detalle_cliente(request, id):
    cliente = buscar_cliente(id)
    if cliente is None:
        return redirect('clientes:lista_clientes')

    # El cliente se registra una sola vez; los demás módulos guardan su resumen embebido
    filtro = {'documento': cliente.documento}
    cotizaciones = Cotizacion.objects.filter(cliente=filtro).order_by('-id')
    ventas = Venta.objects.filter(cliente=filtro).order_by('-id')
    facturas = Factura.objects.filter(cliente=filtro).order_by('-id')

    return render(request, 'clientes_vehiculos/detalle_cliente.html', {
        'cliente': cliente,
        'cotizaciones': cotizaciones,
        'ventas': ventas,
        'facturas': facturas,
        'total_compras': sum(v.precio_final for v in ventas if v.estado == 'activa'),
    })


def editar_cliente(request, id):
    cliente = buscar_cliente(id)
    if cliente is None:
        return redirect('clientes:lista_clientes')

    if request.method == 'POST':
        formulario = FormularioCliente(request.POST, editando=True,
                                       initial={'documento': cliente.documento})
        if formulario.is_valid():
            datos = formulario.cleaned_data
            cliente.tipo_documento = datos['tipo_documento']
            cliente.nombre = datos['nombre']
            cliente.apellido = datos['apellido']
            cliente.email = datos['email']
            cliente.telefono = datos['telefono']
            cliente.fecha_nacimiento = datos['fecha_nacimiento']
            cliente.direccion = direccion_desde(datos)
            cliente.save()
            # Las cotizaciones abiertas se actualizan con los nuevos datos de contacto
            for cotizacion in Cotizacion.objects.filter(cliente={'documento': cliente.documento}):
                if cotizacion.estado in ('pendiente', 'aprobada'):
                    cotizacion.cliente = cliente.resumen()
                    cotizacion.save()
            return redirect('clientes:detalle_cliente', id=cliente.id)
    else:
        direccion = cliente.direccion or {}
        formulario = FormularioCliente(editando=True, initial={
            'tipo_documento': cliente.tipo_documento,
            'documento': cliente.documento,
            'nombre': cliente.nombre,
            'apellido': cliente.apellido,
            'telefono': cliente.telefono,
            'email': cliente.email,
            'fecha_nacimiento': cliente.fecha_nacimiento,
            'ciudad': direccion.get('ciudad', ''),
            'barrio': direccion.get('barrio', ''),
            'calle': direccion.get('calle', ''),
        })

    return render(request, 'clientes_vehiculos/formulario_cliente.html', {
        'formulario': formulario,
        'titulo': f'Editar cliente {cliente.nombre_completo()}',
        'cliente': cliente,
    })


def eliminar_cliente(request, id):
    cliente = buscar_cliente(id)
    if cliente is None:
        return redirect('clientes:lista_clientes')

    filtro = {'documento': cliente.documento}
    bloqueado = Venta.objects.filter(cliente=filtro).exists() or Factura.objects.filter(cliente=filtro).exists()

    if request.method == 'POST' and not bloqueado:
        Cotizacion.objects.filter(cliente=filtro).delete()
        cliente.delete()
        return redirect('clientes:lista_clientes')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar cliente',
        'objeto': f'{cliente.nombre_completo()} · {cliente.documento}',
        'bloqueado': bloqueado,
        'motivo': 'El cliente tiene ventas o facturas registradas y no se puede eliminar.',
        'advertencia': 'También se eliminarán sus cotizaciones.',
        'url_cancelar': 'clientes:detalle_cliente',
        'id_cancelar': cliente.id,
    })


# ---------------- Vehículos ----------------

def catalogo_vehiculos(request):
    vehiculos = Vehiculo.objects.all().order_by('-id')
    busqueda = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '')
    tipo = request.GET.get('tipo', '')

    if busqueda:
        vehiculos = vehiculos.filter(
            Q(marca__icontains=busqueda) | Q(modelo__icontains=busqueda) | Q(placa__icontains=busqueda)
        )
    if estado:
        vehiculos = vehiculos.filter(estado=estado)
    if tipo:
        vehiculos = vehiculos.filter(tipo=tipo)

    return render(request, 'clientes_vehiculos/catalogo_vehiculos.html', {
        'vehiculos': vehiculos,
        'busqueda': busqueda,
        'estado': estado,
        'tipo': tipo,
        'estados': ESTADOS_VEHICULO,
        'tipos': TIPOS_VEHICULO,
        'disponibles': Vehiculo.objects.filter(estado='disponible').count(),
        'total': Vehiculo.objects.count(),
    })


def crear_vehiculo(request):
    if request.method == 'POST':
        formulario = FormularioVehiculo(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            if Vehiculo.objects.filter(placa=datos['placa']).exists():
                formulario.add_error('placa', 'Ya existe un vehículo con esa placa.')
            else:
                vehiculo = Vehiculo(
                    placa=datos['placa'],
                    marca=datos['marca'],
                    modelo=datos['modelo'],
                    anio=datos['anio'],
                    color=datos['color'],
                    tipo=datos['tipo'],
                    condicion=datos['condicion'],
                    estado=datos['estado'],
                    precio=datos['precio'],
                    kilometraje=datos['kilometraje'],
                    imagen_url=datos['imagen_url'],
                    descripcion=datos['descripcion'],
                    ficha_tecnica=ficha_desde(datos),
                )
                vehiculo.save()
                return redirect('clientes:detalle_vehiculo', id=vehiculo.id)
    else:
        formulario = FormularioVehiculo()

    return render(request, 'clientes_vehiculos/formulario_vehiculo.html', {
        'formulario': formulario,
        'titulo': 'Nuevo vehículo',
    })


def detalle_vehiculo(request, id):
    vehiculo = buscar_vehiculo(id)
    if vehiculo is None:
        return redirect('clientes:catalogo_vehiculos')

    filtro = {'placa': vehiculo.placa}
    return render(request, 'clientes_vehiculos/detalle_vehiculo.html', {
        'vehiculo': vehiculo,
        'historial': HistorialVehiculo.objects.filter(vehiculo=filtro).first(),
        'cotizaciones': Cotizacion.objects.filter(vehiculo=filtro).order_by('-id'),
        'venta': Venta.objects.filter(vehiculo=filtro, estado='activa').first(),
    })


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
            vehiculo.tipo = datos['tipo']
            vehiculo.condicion = datos['condicion']
            vehiculo.estado = datos['estado']
            vehiculo.precio = datos['precio']
            vehiculo.kilometraje = datos['kilometraje']
            vehiculo.imagen_url = datos['imagen_url']
            vehiculo.descripcion = datos['descripcion']
            vehiculo.ficha_tecnica = ficha_desde(datos)
            vehiculo.save()
            # El historial guarda un resumen del vehículo: se mantiene sincronizado
            for historial in HistorialVehiculo.objects.filter(vehiculo={'placa': vehiculo.placa}):
                historial.vehiculo = vehiculo.resumen()
                historial.save()
            return redirect('clientes:detalle_vehiculo', id=vehiculo.id)
    else:
        ficha = vehiculo.ficha_tecnica or {}
        formulario = FormularioVehiculo(editando=True, initial={
            'placa': vehiculo.placa,
            'marca': vehiculo.marca,
            'modelo': vehiculo.modelo,
            'anio': vehiculo.anio,
            'color': vehiculo.color,
            'tipo': vehiculo.tipo,
            'condicion': vehiculo.condicion,
            'estado': vehiculo.estado,
            'precio': vehiculo.precio,
            'kilometraje': vehiculo.kilometraje,
            'imagen_url': vehiculo.imagen_url,
            'descripcion': vehiculo.descripcion,
            'motor': ficha.get('motor', ''),
            'cilindraje': ficha.get('cilindraje'),
            'transmision': ficha.get('transmision'),
            'combustible': ficha.get('combustible'),
            'puertas': ficha.get('puertas', 4),
        })

    return render(request, 'clientes_vehiculos/formulario_vehiculo.html', {
        'formulario': formulario,
        'titulo': f'Editar {vehiculo.marca} {vehiculo.modelo}',
        'vehiculo': vehiculo,
    })


def eliminar_vehiculo(request, id):
    vehiculo = buscar_vehiculo(id)
    if vehiculo is None:
        return redirect('clientes:catalogo_vehiculos')

    filtro = {'placa': vehiculo.placa}
    bloqueado = Venta.objects.filter(vehiculo=filtro).exists() or Factura.objects.filter(vehiculo=filtro).exists()

    if request.method == 'POST' and not bloqueado:
        Cotizacion.objects.filter(vehiculo=filtro).delete()
        HistorialVehiculo.objects.filter(vehiculo=filtro).delete()
        vehiculo.delete()
        return redirect('clientes:catalogo_vehiculos')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar vehículo',
        'objeto': str(vehiculo),
        'bloqueado': bloqueado,
        'motivo': 'El vehículo ya tiene una venta o factura registrada y no se puede eliminar.',
        'advertencia': 'También se eliminarán su historial y sus cotizaciones.',
        'url_cancelar': 'clientes:detalle_vehiculo',
        'id_cancelar': vehiculo.id,
    })
