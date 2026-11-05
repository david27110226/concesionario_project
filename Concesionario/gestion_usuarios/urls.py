from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', views.login, name='login'),
    path('registro/', views.registro, name='registro'),
    path('salir/', views.logout, name='logout'),
    path('', views.lista_usuarios, name='lista_usuarios'),
    path('nuevo/', views.crear_usuario, name='crear_usuario'),
    path('<int:id>/', views.detalle_usuario, name='detalle_usuario'),
    path('<int:id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('<int:id>/estado/', views.cambiar_estado_usuario, name='cambiar_estado_usuario'),
    path('<int:id>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    path('<int:id>/metas/nueva/', views.agregar_meta, name='agregar_meta'),
    path('<int:id>/metas/<int:indice>/eliminar/', views.eliminar_meta, name='eliminar_meta'),
    path('notificaciones/', views.notificaciones, name='notificaciones'),
    path('notificaciones/nueva/', views.enviar_notificacion, name='enviar_notificacion'),
    path('notificaciones/<int:indice>/leer/', views.leer_notificacion, name='leer_notificacion'),
    path('notificaciones/<int:indice>/eliminar/', views.eliminar_notificacion, name='eliminar_notificacion'),
]
