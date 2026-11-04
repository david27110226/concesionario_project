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
    path('promociones/', views.lista_promociones, name='lista_promociones'),
    path('promociones/nueva/', views.crear_promocion, name='crear_promocion'),
    path('promociones/<int:id>/editar/', views.editar_promocion, name='editar_promocion'),
    path('promociones/<int:id>/eliminar/', views.eliminar_promocion, name='eliminar_promocion'),
    path('seguimientos/', views.lista_seguimientos, name='lista_seguimientos'),
    path('seguimientos/nuevo/', views.crear_seguimiento, name='crear_seguimiento'),
    path('seguimientos/<int:id>/editar/', views.editar_seguimiento, name='editar_seguimiento'),
    path('seguimientos/<int:id>/eliminar/', views.eliminar_seguimiento, name='eliminar_seguimiento'),
    path('entregas/', views.lista_entregas, name='lista_entregas'),
    path('entregas/nueva/', views.crear_entrega, name='crear_entrega'),
    path('entregas/<int:id>/editar/', views.editar_entrega, name='editar_entrega'),
    path('entregas/<int:id>/eliminar/', views.eliminar_entrega, name='eliminar_entrega'),
    path('garantias/', views.lista_garantias, name='lista_garantias'),
    path('garantias/nueva/', views.crear_garantia, name='crear_garantia'),
    path('garantias/<int:id>/editar/', views.editar_garantia, name='editar_garantia'),
    path('garantias/<int:id>/eliminar/', views.eliminar_garantia, name='eliminar_garantia'),
]
