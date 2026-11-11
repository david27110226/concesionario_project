from django.urls import path

from . import views

app_name = 'historial'

urlpatterns = [
    path('', views.lista_historiales, name='lista_historiales'),
    path('mantenimientos/', views.lista_mantenimientos, name='lista_mantenimientos'),
    path('<int:id>/', views.detalle_historial, name='detalle_historial'),
    path('<int:id>/propietarios/nuevo/', views.agregar_propietario, name='agregar_propietario'),
    path('<int:id>/propietarios/<int:indice>/editar/', views.editar_propietario, name='editar_propietario'),
    path('<int:id>/propietarios/<int:indice>/eliminar/', views.eliminar_propietario, name='eliminar_propietario'),
    path('<int:id>/mantenimientos/nuevo/', views.agregar_mantenimiento, name='agregar_mantenimiento'),
    path('<int:id>/mantenimientos/<int:indice>/editar/', views.editar_mantenimiento, name='editar_mantenimiento'),
    path('<int:id>/mantenimientos/<int:indice>/eliminar/', views.eliminar_mantenimiento,
         name='eliminar_mantenimiento'),
    path('<int:id>/siniestros/nuevo/', views.agregar_siniestro, name='agregar_siniestro'),
    path('<int:id>/siniestros/<int:indice>/editar/', views.editar_siniestro, name='editar_siniestro'),
    path('<int:id>/siniestros/<int:indice>/eliminar/', views.eliminar_siniestro, name='eliminar_siniestro'),
]
