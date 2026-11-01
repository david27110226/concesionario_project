from django.urls import path

from . import views

app_name = 'ventas'

urlpatterns = [
    path('', views.lista_ventas, name='lista_ventas'),
    path('nueva/', views.crear_venta, name='crear_venta'),
    path('<int:id>/', views.detalle_venta, name='detalle_venta'),
    path('<int:id>/editar/', views.editar_venta, name='editar_venta'),
    path('<int:id>/anular/', views.anular_venta, name='anular_venta'),
    path('<int:id>/eliminar/', views.eliminar_venta, name='eliminar_venta'),
    path('cotizaciones/', views.lista_cotizaciones, name='lista_cotizaciones'),
    path('cotizaciones/nueva/', views.crear_cotizacion, name='crear_cotizacion'),
    path('cotizaciones/<int:id>/', views.detalle_cotizacion, name='detalle_cotizacion'),
    path('cotizaciones/<int:id>/editar/', views.editar_cotizacion, name='editar_cotizacion'),
    path('cotizaciones/<int:id>/estado/<str:estado>/', views.cambiar_estado_cotizacion,
         name='cambiar_estado_cotizacion'),
    path('cotizaciones/<int:id>/vender/', views.vender_cotizacion, name='vender_cotizacion'),
    path('cotizaciones/<int:id>/eliminar/', views.eliminar_cotizacion, name='eliminar_cotizacion'),
]
