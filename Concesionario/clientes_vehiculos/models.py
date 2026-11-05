from djongo import models

# PropietarioAnterior y Mantenimiento se definen una sola vez en historial_vehiculo
from historial_vehiculo.models import Mantenimiento, PropietarioAnterior


class Vehiculo(models.Model):
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('reservado', 'Reservado'),
        ('vendido', 'Vendido'),
    ]
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.IntegerField()
    color = models.CharField(max_length=30, blank=True)
    placa = models.CharField(max_length=10, unique=True)
    precio = models.FloatField(null=True, blank=True)
    kilometraje = models.IntegerField(default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')
    descripcion = models.TextField(blank=True)
    fecha_ingreso = models.DateField(auto_now_add=True)
    fecha_actualizacion = models.DateField(auto_now=True)
    propietarios_anteriores = models.ArrayField(
        model_container=PropietarioAnterior,
        blank=True
    )
    mantenimientos = models.ArrayField(
        model_container=Mantenimiento,
        blank=True
    )

    class Meta:
        db_table = 'vehiculos'

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.anio})"


class VehiculoCotizacion(models.Model):
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.IntegerField()
    placa = models.CharField(max_length=10)
    precio = models.FloatField(null=True, blank=True)

    class Meta:
        abstract = True


class DetalleVendedor(models.Model):
    nombre_usuario = models.CharField(max_length=150)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)

    class Meta:
        abstract = True


class Venta(models.Model):
    fecha_venta = models.DateField(null=True, blank=True)
    precio_final = models.FloatField(null=True, blank=True)
    forma_pago = models.CharField(max_length=50, blank=True)
    # La factura vive solo en la colección facturas (pagos_facturacion);
    # aquí se guarda únicamente su número para no repetirla.
    numero_factura = models.CharField(max_length=20, blank=True)

    class Meta:
        abstract = True


class Cotizacion(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    vehiculo = models.EmbeddedField(model_container=VehiculoCotizacion)
    vendedor = models.EmbeddedField(model_container=DetalleVendedor)
    precio_ofertado = models.FloatField(null=True, blank=True)
    fecha = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    notas = models.TextField(blank=True)
    venta = models.EmbeddedField(
        model_container=Venta,
        null=True,
        blank=True
    )

    class Meta:
        abstract = True


class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20)
    direccion = models.TextField(blank=True)
    fecha_registro = models.DateField(auto_now_add=True)
    cotizaciones = models.ArrayField(
        model_container=Cotizacion,
        blank=True
    )

    class Meta:
        db_table = 'clientes'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
