from djongo import models

from clientes_vehiculos.models import VehiculoResumen


TIPOS_MANTENIMIENTO = [
    ('cambio_aceite', 'Cambio de aceite'),
    ('frenos', 'Revisión de frenos'),
    ('llantas', 'Cambio de llantas'),
    ('revision_general', 'Revisión general'),
    ('electrico', 'Sistema eléctrico'),
    ('latoneria', 'Latonería y pintura'),
    ('otro', 'Otro'),
]

ESPECIALIDADES = [
    ('general', 'Mecánica general'),
    ('electrico', 'Eléctrico'),
    ('latoneria', 'Latonería y pintura'),
    ('llantas', 'Llantas y alineación'),
    ('concesionario', 'Taller del concesionario'),
]


# ---------- Clases embebidas (abstract) ----------

class PropietarioAnterior(models.Model):
    nombre = models.CharField(max_length=150)
    documento = models.CharField(max_length=20, blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        abstract = True


class Mantenimiento(models.Model):
    tipo = models.CharField(max_length=30, choices=TIPOS_MANTENIMIENTO)
    descripcion = models.CharField(max_length=300, blank=True)
    fecha = models.DateField()
    kilometraje = models.IntegerField()
    costo = models.FloatField()
    taller = models.CharField(max_length=100)

    class Meta:
        abstract = True


# ---------- Colecciones ----------

class Taller(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    nit = models.CharField(max_length=20)
    telefono = models.CharField(max_length=20)
    ciudad = models.CharField(max_length=60)
    especialidad = models.CharField(max_length=20, choices=ESPECIALIDADES, default='general')
    fecha_registro = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'talleres'

    def __str__(self):
        return self.nombre


class HistorialVehiculo(models.Model):
    vehiculo = models.EmbeddedField(model_container=VehiculoResumen)
    observaciones = models.TextField(blank=True)
    propietarios_anteriores = models.ArrayField(model_container=PropietarioAnterior, blank=True)
    mantenimientos = models.ArrayField(model_container=Mantenimiento, blank=True)
    fecha_creacion = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'historiales'

    def __str__(self):
        return f"Historial {self.vehiculo['placa']}"

    def costo_total(self):
        return sum(m['costo'] for m in self.mantenimientos)
