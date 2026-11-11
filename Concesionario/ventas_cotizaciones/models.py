from djongo import models

# ResumenUsuario se define una sola vez en gestion_usuarios
from gestion_usuarios.models import ResumenUsuario


class VehiculoCotizacion(models.Model):
    """Copia del vehículo al momento de cotizar (el precio puede cambiar después)."""
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.IntegerField()
    placa = models.CharField(max_length=10)
    precio = models.FloatField(null=True, blank=True)

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
    """Colección propia: así vehiculo, vendedor y venta quedan a un solo nivel
    (antes estaban dentro de la cotización que a su vez estaba dentro del cliente)."""
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    id_cliente = models.IntegerField()
    vehiculo = models.EmbeddedField(model_container=VehiculoCotizacion)
    vendedor = models.EmbeddedField(model_container=ResumenUsuario)
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
        db_table = 'cotizaciones'

    def __str__(self):
        return f"Cotización {self.id} · {self.vehiculo['placa']}"


class Condicion(models.Model):
    titulo = models.CharField(max_length=150)
    contenido = models.TextField()
    orden = models.IntegerField(default=1)

    class Meta:
        abstract = True


class Descuento(models.Model):
    nombre = models.CharField(max_length=100)
    porcentaje = models.FloatField()
    descripcion = models.TextField(blank=True)

    class Meta:
        abstract = True


class PlantillaCotizacion(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateField(auto_now_add=True)
    fecha_actualizacion = models.DateField(auto_now=True)
    creado_por = models.EmbeddedField(model_container=ResumenUsuario)
    condiciones = models.ArrayField(model_container=Condicion, blank=True)
    descuentos = models.ArrayField(model_container=Descuento, blank=True)
    notas_adicionales = models.TextField(blank=True)

    class Meta:
        db_table = 'plantillasCotizacion'

    def __str__(self):
        return self.nombre
