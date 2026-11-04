import calendar

from djongo import models
from clientes_vehiculos.models import Cliente, Vehiculo
from gestion_usuarios.models import Usuario


ESTADOS_COTIZACION = [
    ('pendiente', 'Pendiente'),
    ('aprobada', 'Aprobada'),
    ('rechazada', 'Rechazada'),
    ('vendida', 'Vendida'),
]

FORMAS_PAGO = [
    ('contado', 'Contado'),
    ('credito', 'Credito'),
    ('leasing', 'Leasing'),
]

ESTADOS_VENTA = [
    ('activa', 'Activa'),
    ('anulada', 'Anulada'),
]

MEDIOS_CONTACTO = [
    ('llamada', 'Llamada'),
    ('whatsapp', 'WhatsApp'),
    ('correo', 'Correo'),
    ('visita', 'Visita al concesionario'),
]

RESULTADOS_SEGUIMIENTO = [
    ('interesado', 'Interesado'),
    ('en_proceso', 'En proceso'),
    ('sin_respuesta', 'Sin respuesta'),
    ('descartado', 'Descartado'),
]

ESTADOS_ENTREGA = [
    ('programada', 'Programada'),
    ('reprogramada', 'Reprogramada'),
    ('entregada', 'Entregada'),
    ('cancelada', 'Cancelada'),
]

TIPOS_GARANTIA = [
    ('basica', 'Basica'),
    ('extendida', 'Extendida'),
    ('motor', 'Motor y transmision'),
]

ESTADOS_GARANTIA = [
    ('vigente', 'Vigente'),
    ('vencida', 'Vencida'),
    ('anulada', 'Anulada'),
]


TONO_ESTADO = {
    'interesado': 'activa', 'en_proceso': 'pendiente', 'sin_respuesta': 'info', 'descartado': 'anulada',
    'programada': 'pendiente', 'reprogramada': 'info', 'entregada': 'activa', 'cancelada': 'anulada',
    'vigente': 'activa', 'vencida': 'pendiente', 'anulada': 'anulada',
}


class Promocion(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.CharField(max_length=250, blank=True)
    porcentaje = models.FloatField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = 'promociones'

    def __str__(self):
        return f"{self.nombre} ({self.porcentaje:g} %)"

    def esta_vigente(self, hoy):
        return self.activa and self.fecha_inicio <= hoy <= self.fecha_fin


class Cotizacion(models.Model):
    numero = models.CharField(max_length=20, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='cotizaciones')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name='cotizaciones')
    vendedor = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='cotizaciones')
    promocion = models.ForeignKey(Promocion, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='cotizaciones')
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
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='ventas')
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='ventas')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name='ventas')
    vendedor = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='ventas')
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


class Seguimiento(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='seguimientos')
    fecha = models.DateField()
    medio = models.CharField(max_length=20, choices=MEDIOS_CONTACTO, default='llamada')
    resultado = models.CharField(max_length=20, choices=RESULTADOS_SEGUIMIENTO, default='en_proceso')
    comentario = models.CharField(max_length=300)
    proxima_fecha = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'seguimientos'

    def __str__(self):
        return f"{self.cotizacion.numero} · {self.fecha}"

    @property
    def tono(self):
        return TONO_ESTADO[self.resultado]


class Entrega(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='entregas')
    fecha_programada = models.DateField()
    fecha_entrega = models.DateField(null=True, blank=True)
    lugar = models.CharField(max_length=120)
    estado = models.CharField(max_length=20, choices=ESTADOS_ENTREGA, default='programada')
    observaciones = models.CharField(max_length=300, blank=True)

    class Meta:
        db_table = 'entregas'

    def __str__(self):
        return f"Entrega {self.venta.numero}"

    @property
    def tono(self):
        return TONO_ESTADO[self.estado]


class Garantia(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='garantias')
    tipo = models.CharField(max_length=20, choices=TIPOS_GARANTIA, default='basica')
    meses = models.PositiveIntegerField(default=12)
    kilometraje_limite = models.PositiveIntegerField(default=20000)
    fecha_inicio = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS_GARANTIA, default='vigente')
    cobertura = models.CharField(max_length=300, blank=True)

    class Meta:
        db_table = 'garantias'

    def __str__(self):
        return f"Garantia {self.get_tipo_display()} · {self.venta.numero}"

    @property
    def fecha_fin(self):
        mes = self.fecha_inicio.month - 1 + self.meses
        anio = self.fecha_inicio.year + mes // 12
        mes = mes % 12 + 1
        dia = min(self.fecha_inicio.day, calendar.monthrange(anio, mes)[1])
        return self.fecha_inicio.replace(year=anio, month=mes, day=dia)

    @property
    def tono(self):
        return TONO_ESTADO[self.estado]
