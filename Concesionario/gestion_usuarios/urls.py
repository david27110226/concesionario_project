from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.lista_usuarios, name='lista_usuarios'),
    path('nuevo/', views.crear_usuario, name='crear_usuario'),
    path('<int:id>/', views.detalle_usuario, name='detalle_usuario'),
    path('<int:id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('<int:id>/estado/', views.cambiar_estado_usuario, name='cambiar_estado_usuario'),
    path('<int:id>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    path('roles/', views.lista_roles, name='lista_roles'),
    path('roles/nuevo/', views.crear_rol, name='crear_rol'),
    path('roles/<int:id>/editar/', views.editar_rol, name='editar_rol'),
    path('roles/<int:id>/eliminar/', views.eliminar_rol, name='eliminar_rol'),
]
