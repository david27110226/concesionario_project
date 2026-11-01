from djongo import models


TIPOS_DOCUMENTO = [
    ('CC', 'Cédula de ciudadanía'),
    ('CE', 'Cédula de extranjería'),
    ('NIT', 'NIT'),
    ('PAS', 'Pasaporte'),
]

TIPOS_VEHICULO = [
    ('sedan', 'Sedán'),
    ('hatchback', 'Hatchback'),
    ('suv', 'SUV'),
    ('camioneta', 'Camioneta'),
    ('pickup', 'Pick-up'),
    ('deportivo', 'Deportivo'),
]

ESTADOS_VEHICULO = [
    ('disponible', 'Disponible'),
    ('reservado', 'Reservado'),
    ('vendido', 'Vendido'),
]

CONDICIONES = [
    ('nuevo', 'Nuevo'),
    ('usado', 'Usado'),
]

TRANSMISIONES = [
    ('manual', 'Manual'),
    ('automatica', 'Automática'),
]

COMBUSTIBLES = [
    ('gasolina', 'Gasolina'),
    ('diesel', 'Diésel'),
    ('hibrido', 'Híbrido'),
    ('electrico', 'Eléctrico'),
]


# ---------- Clases embebidas (abstract) ----------

class Direccion(models.Model):
    ciudad = models.CharField(max_length=60)
    barrio = models.CharField(max_length=60, blank=True)
    calle = models.CharField(max_length=120)

    class Meta:
        abstract = True


class FichaTecnica(models.Model):
    motor = models.CharField(max_length=50)
    cilindraje = models.IntegerField()
    transmision = models.CharField(max_length=20, choices=TRANSMISIONES)
    combustible = models.CharField(max_length=20, choices=COMBUSTIBLES)
    puertas = models.IntegerField()

    class Meta:
        abstract = True


class ClienteResumen(models.Model):
    """Datos mínimos del cliente que viajan dentro de cotizaciones,
    ventas, facturas e historiales."""
    documento = models.CharField(max_length=20)
    nombre_completo = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True)

    class Meta:
        abstract = True


class VehiculoResumen(models.Model):
    """Datos mínimos del vehículo que viajan dentro de otros documentos."""
    placa = models.CharField(max_length=10)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.IntegerField()

    class Meta:
        abstract = True


# ---------- Colecciones ----------

class Cliente(models.Model):
    tipo_documento = models.CharField(max_length=5, choices=TIPOS_DOCUMENTO, default='CC')
    documento = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    direccion = models.EmbeddedField(model_container=Direccion, null=True, blank=True)
    fecha_registro = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'clientes'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def resumen(self):
        return {
            'documento': self.documento,
            'nombre_completo': self.nombre_completo(),
            'telefono': self.telefono,
            'email': self.email,
        }


class Vehiculo(models.Model):
    placa = models.CharField(max_length=10, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.IntegerField()
    color = models.CharField(max_length=30)
    tipo = models.CharField(max_length=20, choices=TIPOS_VEHICULO, default='sedan')
    condicion = models.CharField(max_length=10, choices=CONDICIONES, default='nuevo')
    precio = models.FloatField()
    kilometraje = models.IntegerField(default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS_VEHICULO, default='disponible')
    imagen_url = models.URLField(blank=True)
    descripcion = models.TextField(blank=True)
    ficha_tecnica = models.EmbeddedField(model_container=FichaTecnica, null=True, blank=True)
    fecha_ingreso = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'vehiculos'

    def __str__(self):
        return f"{self.marca} {self.modelo} {self.anio} ({self.placa})"

    def resumen(self):
        return {
            'placa': self.placa,
            'marca': self.marca,
            'modelo': self.modelo,
            'anio': self.anio,
        }
