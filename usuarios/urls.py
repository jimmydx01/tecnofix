from django.urls import path

from . import views, views_admin

urlpatterns = [
    path('ingresar/', views.ingresar, name='ingresar'),
    path('registro/', views.registro, name='registro'),
    path('panel/personal/', views_admin.personal, name='personal'),
    path('panel/clientes/', views_admin.clientes, name='clientes'),
    path('cuenta/contrasena/', views.cambiar_contrasena, name='cambiar_contrasena'),
    path('panel/usuarios/<int:pk>/contrasena/', views_admin.restablecer_contrasena, name='usuario_contrasena'),
    path('panel/usuarios/<int:pk>/estado/', views_admin.usuario_estado, name='usuario_estado'),
    path('panel/usuarios/<int:pk>/eliminar/', views_admin.usuario_eliminar, name='usuario_eliminar'),
]
