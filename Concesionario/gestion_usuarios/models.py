from djongo import models


MODULOS = [
    ('usuarios', 'Gestión de usuarios'),
    ('clientes', 'Clientes y vehículos'),
    ('historial', 'Historial de vehículos'),
    ('ventas', 'Ventas y cotizaciones'),
    ('pagos', 'Pagos y facturación'),
]

NIVELES = [
    ('lectura', 'Solo lectura'),
    ('escritura', 'Lectura y escritura'),
    ('total', 'Control total'),
]

CARGOS = [
    ('administrador', 'Administrador'),
    ('vendedor', 'Asesor de ventas'),
    ('cajero', 'Cajero'),
    ('tecnico', 'Técnico'),
    ('gerente', 'Gerente'),
]


# ---------- Clases embebidas (abstract) ----------

class Permiso(models.Model):
    modulo = models.CharField(max_length=20, choices=MODULOS)
    nivel = models.CharField(max_length=20, choices=NIVELES)

    class Meta:
        abstract = True


class RolAsignado(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=200, blank=True)

    class Meta:
        abstract = True


class UsuarioResumen(models.Model):
    """Datos mínimos de un usuario que se guardan dentro de cotizaciones,
    ventas o mantenimientos (no se carga todo el usuario)."""
    nombre_usuario = models.CharField(max_length=150)
    nombre_completo = models.CharField(max_length=200)

    class Meta:
        abstract = True


# ---------- Colecciones ----------

class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=200, blank=True)
    permisos = models.ArrayField(model_container=Permiso, blank=True)
    fecha_creacion = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return self.nombre


class Usuario(models.Model):
    nombre_usuario = models.CharField(max_length=150, unique=True)
    contrasena = models.CharField(max_length=255)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True)
    cargo = models.CharField(max_length=20, choices=CARGOS, default='vendedor')
    activo = models.BooleanField(default=True)
    rol = models.EmbeddedField(model_container=RolAsignado, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return self.nombre_usuario

    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def resumen(self):
        return {
            'nombre_usuario': self.nombre_usuario,
            'nombre_completo': self.nombre_completo(),
        }
