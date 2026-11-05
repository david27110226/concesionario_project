from djongo import models


class CreadoPor(models.Model):
    nombre_usuario = models.CharField(max_length=150)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)

    class Meta:
        abstract = True


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
    creado_por = models.EmbeddedField(model_container=CreadoPor)
    condiciones = models.ArrayField(model_container=Condicion, blank=True)
    descuentos = models.ArrayField(model_container=Descuento, blank=True)
    notas_adicionales = models.TextField(blank=True)

    class Meta:
        db_table = 'plantillasCotizacion'

    def __str__(self):
        return self.nombre
