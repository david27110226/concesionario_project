from django.urls import path

from . import views

app_name = 'historial'

urlpatterns = [
    path('', views.lista_historiales, name='lista_historiales'),
    path('nuevo/', views.crear_historial, name='crear_historial'),
    path('<int:id>/', views.detalle_historial, name='detalle_historial'),
    path('<int:id>/editar/', views.editar_historial, name='editar_historial'),
    path('<int:id>/eliminar/', views.eliminar_historial, name='eliminar_historial'),
    path('<int:id>/mantenimientos/nuevo/', views.agregar_mantenimiento, name='agregar_mantenimiento'),
    path('<int:id>/mantenimientos/<int:indice>/eliminar/', views.eliminar_mantenimiento,
         name='eliminar_mantenimiento'),
    path('<int:id>/propietarios/nuevo/', views.agregar_propietario, name='agregar_propietario'),
    path('<int:id>/propietarios/<int:indice>/eliminar/', views.eliminar_propietario,
         name='eliminar_propietario'),
    path('talleres/', views.lista_talleres, name='lista_talleres'),
    path('talleres/nuevo/', views.crear_taller, name='crear_taller'),
    path('talleres/<int:id>/editar/', views.editar_taller, name='editar_taller'),
    path('talleres/<int:id>/eliminar/', views.eliminar_taller, name='eliminar_taller'),
]
