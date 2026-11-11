from djongo import models

# PropietarioAnterior, Mantenimiento y Siniestro se definen una sola vez en historial_vehiculo
from historial_vehiculo.models import Mantenimiento, PropietarioAnterior, Siniestro


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
    siniestros = models.ArrayField(
        model_container=Siniestro,
        blank=True,
        default=list
    )

    class Meta:
        db_table = 'vehiculos'

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.anio})"


class Seguimiento(models.Model):
    """Contacto del asesor con el cliente (llamada, visita, correo...)."""
    MEDIOS = [
        ('llamada', 'Llamada'),
        ('visita', 'Visita'),
        ('correo', 'Correo'),
        ('whatsapp', 'WhatsApp'),
    ]
    fecha = models.DateField()
    medio = models.CharField(max_length=20, choices=MEDIOS)
    comentario = models.TextField()
    asesor = models.CharField(max_length=150)

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
    # Las cotizaciones viven en su propia colección (ventas_cotizaciones)
    # para no tener objetos dentro de objetos.
    seguimientos = models.ArrayField(
        model_container=Seguimiento,
        blank=True,
        default=list
    )

    class Meta:
        db_table = 'clientes'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
