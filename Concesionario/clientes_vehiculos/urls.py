from django.urls import path

from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.lista_clientes, name='lista_clientes'),
    path('nuevo/', views.crear_cliente, name='crear_cliente'),
    path('<int:id>/', views.detalle_cliente, name='detalle_cliente'),
    path('<int:id>/editar/', views.editar_cliente, name='editar_cliente'),
    path('<int:id>/eliminar/', views.eliminar_cliente, name='eliminar_cliente'),
    path('vehiculos/', views.catalogo_vehiculos, name='catalogo_vehiculos'),
    path('vehiculos/nuevo/', views.crear_vehiculo, name='crear_vehiculo'),
    path('vehiculos/<int:id>/', views.detalle_vehiculo, name='detalle_vehiculo'),
    path('vehiculos/<int:id>/editar/', views.editar_vehiculo, name='editar_vehiculo'),
    path('vehiculos/<int:id>/eliminar/', views.eliminar_vehiculo, name='eliminar_vehiculo'),
]
