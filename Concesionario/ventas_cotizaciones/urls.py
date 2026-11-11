from django.urls import path

from . import views

app_name = 'ventas'

urlpatterns = [
    path('', views.lista_ventas, name='lista_ventas'),
    path('cotizaciones/', views.lista_cotizaciones, name='lista_cotizaciones'),
    path('cotizaciones/nueva/', views.crear_cotizacion, name='crear_cotizacion'),
    path('cotizaciones/<int:id>/', views.detalle_cotizacion, name='detalle_cotizacion'),
    path('cotizaciones/<int:id>/editar/', views.editar_cotizacion, name='editar_cotizacion'),
    path('cotizaciones/<int:id>/estado/<str:estado>/', views.cambiar_estado_cotizacion,
         name='cambiar_estado_cotizacion'),
    path('cotizaciones/<int:id>/eliminar/', views.eliminar_cotizacion, name='eliminar_cotizacion'),
    path('cotizaciones/<int:id>/venta/', views.registrar_venta, name='registrar_venta'),
    path('cotizaciones/<int:id>/venta/eliminar/', views.eliminar_venta, name='eliminar_venta'),
    path('plantillas/', views.lista_plantillas, name='lista_plantillas'),
    path('plantillas/nueva/', views.crear_plantilla, name='crear_plantilla'),
    path('plantillas/<int:id>/', views.detalle_plantilla, name='detalle_plantilla'),
    path('plantillas/<int:id>/editar/', views.editar_plantilla, name='editar_plantilla'),
    path('plantillas/<int:id>/eliminar/', views.eliminar_plantilla, name='eliminar_plantilla'),
    path('plantillas/<int:id>/condiciones/nueva/', views.agregar_condicion, name='agregar_condicion'),
    path('plantillas/<int:id>/condiciones/<int:indice>/eliminar/', views.eliminar_condicion,
         name='eliminar_condicion'),
    path('plantillas/<int:id>/descuentos/nuevo/', views.agregar_descuento, name='agregar_descuento'),
    path('plantillas/<int:id>/descuentos/<int:indice>/eliminar/', views.eliminar_descuento,
         name='eliminar_descuento'),
]
