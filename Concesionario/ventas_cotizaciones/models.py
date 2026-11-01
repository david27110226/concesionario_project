from djongo import models

from clientes_vehiculos.models import ClienteResumen, VehiculoResumen
from gestion_usuarios.models import UsuarioResumen


ESTADOS_COTIZACION = [
    ('pendiente', 'Pendiente'),
    ('aprobada', 'Aprobada'),
    ('rechazada', 'Rechazada'),
    ('vendida', 'Vendida'),
]

FORMAS_PAGO = [
    ('contado', 'Contado'),
    ('credito', 'Crédito'),
    ('leasing', 'Leasing'),
]

ESTADOS_VENTA = [
    ('activa', 'Activa'),
    ('anulada', 'Anulada'),
]


class Cotizacion(models.Model):
    numero = models.CharField(max_length=20, unique=True)
    cliente = models.EmbeddedField(model_container=ClienteResumen)
    vehiculo = models.EmbeddedField(model_container=VehiculoResumen)
    vendedor = models.EmbeddedField(model_container=UsuarioResumen)
    precio_base = models.FloatField()
    descuento_porcentaje = models.FloatField(default=0)
    precio_ofertado = models.FloatField()
    fecha = models.DateField()
    vigencia_dias = models.PositiveIntegerField(default=15)
    estado = models.CharField(max_length=20, choices=ESTADOS_COTIZACION, default='pendiente')
    notas = models.TextField(blank=True)

    class Meta:
        db_table = 'cotizaciones'

    def __str__(self):
        return self.numero


class Venta(models.Model):
    numero = models.CharField(max_length=20, unique=True)
    numero_cotizacion = models.CharField(max_length=20, blank=True)
    cliente = models.EmbeddedField(model_container=ClienteResumen)
    vehiculo = models.EmbeddedField(model_container=VehiculoResumen)
    vendedor = models.EmbeddedField(model_container=UsuarioResumen)
    precio_final = models.FloatField()
    forma_pago = models.CharField(max_length=20, choices=FORMAS_PAGO, default='contado')
    fecha_venta = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS_VENTA, default='activa')
    facturada = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True)

    class Meta:
        db_table = 'ventas'

    def __str__(self):
        return self.numero
