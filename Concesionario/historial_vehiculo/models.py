from djongo import models

class PropietarioAnterior(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        abstract = True

class Mantenimiento(models.Model):
    TIPOS = [
        ('cambio_aceite', 'Cambio de aceite'),
        ('frenos', 'Revision de frenos'),
        ('llantas', 'Cambio de llantas'),
        ('revision_general', 'Revision general'),
        ('otro', 'Otro'),
    ]
    tipo = models.CharField(max_length=50, choices=TIPOS)
    descripcion = models.TextField(blank=True)
    fecha = models.DateField()
    costo = models.FloatField(null=True, blank=True)

    class Meta:
        abstract = True
