from djongo import models


class Rol(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)
    perm_clientes = models.BooleanField(default=False)
    perm_ventas = models.BooleanField(default=False)
    perm_historial = models.BooleanField(default=False)
    perm_pagos = models.BooleanField(default=False)
    perm_usuarios = models.BooleanField(default=False)

    class Meta:
        abstract = True


class AuditoriaItem(models.Model):
    ACCIONES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('crear', 'Crear'),
        ('editar', 'Editar'),
        ('eliminar', 'Eliminar'),
        ('ver', 'Ver'),
    ]
    accion = models.CharField(max_length=20, choices=ACCIONES)
    modulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    ip = models.CharField(max_length=45, blank=True)
    fecha = models.DateTimeField()
    exitoso = models.BooleanField(default=True)

    class Meta:
        abstract = True


class MetaVentas(models.Model):
    mes = models.IntegerField()
    anio = models.IntegerField()
    meta_ventas = models.IntegerField(default=0)
    ventas_realizadas = models.IntegerField(default=0)
    fecha_asignacion = models.DateField()

    class Meta:
        abstract = True


class Notificacion(models.Model):
    remitente = models.CharField(max_length=150)
    asunto = models.CharField(max_length=200)
    mensaje = models.TextField()
    fecha = models.DateTimeField()
    leida = models.BooleanField(default=False)
    fecha_lectura = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class Usuario(models.Model):
    nombre_usuario = models.CharField(max_length=150)
    contrasena = models.CharField(max_length=255)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True)
    es_administrador = models.BooleanField(default=False)
    es_superusuario = models.BooleanField(default=False)
    esta_activo = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    rol = models.EmbeddedField(model_container=Rol, null=True, blank=True)
    auditoria = models.ArrayField(model_container=AuditoriaItem, blank=True)
    metas = models.ArrayField(model_container=MetaVentas, blank=True)
    notificaciones = models.ArrayField(model_container=Notificacion, blank=True)

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return self.nombre_usuario