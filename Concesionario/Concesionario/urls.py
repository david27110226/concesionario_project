from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('usuarios/', include('gestion_usuarios.urls')),
    path('clientes/', include('clientes_vehiculos.urls')),
    path('historial/', include('historial_vehiculo.urls')),
    path('ventas/', include('ventas_cotizaciones.urls')),
    path('pagos/', include('pagos_facturacion.urls')),
    path('admin/', admin.site.urls),
]
