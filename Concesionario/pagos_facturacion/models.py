from djongo import models

from clientes_vehiculos.models import ClienteResumen, VehiculoResumen


TIPOS_PAGO = [
    ('efectivo', 'Efectivo'),
    ('tarjeta_credito', 'Tarjeta de crédito'),
    ('tarjeta_debito', 'Tarjeta débito'),
    ('transferencia', 'Transferencia bancaria'),
    ('cheque', 'Cheque'),
]

FORMAS_PAGO = [
    ('contado', 'Contado'),
    ('cuota', 'Cuota'),
]

ESTADOS_FACTURA = [
    ('pendiente', 'Pendiente de pago'),
    ('pagada', 'Pagada'),
    ('anulada', 'Anulada'),
]


# ---------- Clases embebidas (abstract) ----------

class DetallePago(models.Model):
    tipo_pago = models.CharField(max_length=30, choices=TIPOS_PAGO)
    forma_pago = models.CharField(max_length=20, choices=FORMAS_PAGO)
    monto = models.FloatField()
    fecha_pago = models.DateField()
    numero_referencia = models.CharField(max_length=50, blank=True)
    observaciones = models.CharField(max_length=300, blank=True)

    class Meta:
        abstract = True


# ---------- Colecciones ----------

class Factura(models.Model):
    numero_factura = models.CharField(max_length=20, unique=True)
    numero_venta = models.CharField(max_length=20)
    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField()
    cliente = models.EmbeddedField(model_container=ClienteResumen)
    vehiculo = models.EmbeddedField(model_container=VehiculoResumen)
    subtotal = models.FloatField()
    iva_porcentaje = models.FloatField(default=19)
    impuesto_iva = models.FloatField()
    total = models.FloatField()
    estado = models.CharField(max_length=20, choices=ESTADOS_FACTURA, default='pendiente')
    pagos = models.ArrayField(model_container=DetallePago, blank=True)

    class Meta:
        db_table = 'facturas'

    def __str__(self):
        return f"Factura {self.numero_factura}"

    def total_pagado(self):
        return sum(p['monto'] for p in self.pagos)

    def saldo(self):
        return max(self.total - self.total_pagado(), 0)

    def porcentaje_pagado(self):
        if not self.total:
            return 0
        return min(round(self.total_pagado() * 100 / self.total), 100)
