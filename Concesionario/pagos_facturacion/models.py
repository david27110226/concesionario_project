from djongo import models


class DetallePago(models.Model):
    TIPOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('tarjeta_credito', 'Tarjeta de Crédito'),
        ('tarjeta_debito', 'Tarjeta de Débito'),
        ('transferencia', 'Transferencia Bancaria'),
        ('cheque', 'Cheque'),
    ]
    
    FORMA_PAGO = [
        ('contado', 'Contado'),
        ('cuota', 'Cuota'),
    ]

    tipo_pago = models.CharField(max_length=30, choices=TIPOS_PAGO)
    forma_pago = models.CharField(max_length=20, choices=FORMA_PAGO)
    monto = models.FloatField()
    fecha_pago = models.DateField(auto_now_add=True)
    numero_referencia = models.CharField(max_length=50, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        abstract = True


class Factura(models.Model):
    ESTADOS_FACTURA = [
        ('emitida', 'Emitida'),
        ('pagada', 'Pagada'),
        ('anulada', 'Anulada'),
    ]

    numero_factura = models.CharField(max_length=20, unique=True)
    fecha_emision = models.DateField(auto_now_add=True)
    cedula_cliente = models.CharField(max_length=20)
    nombre_cliente = models.CharField(max_length=150)
    placa_vehiculo = models.CharField(max_length=10)
    subtotal = models.FloatField()
    impuesto_iva = models.FloatField()
    total = models.FloatField()
    estado = models.CharField(max_length=20, choices=ESTADOS_FACTURA, default='emitida')
    pagos = models.ArrayField(
        model_container=DetallePago,
        blank=True
    )

    class Meta:
        db_table = 'facturas'

    def __str__(self):
        return f"Factura #{self.numero_factura} - {self.nombre_cliente} ({self.estado})"