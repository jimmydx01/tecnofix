from django.urls import path

from . import views_admin

urlpatterns = [
    path('panel/tarifas/', views_admin.tarifas, name='tarifas'),
    path('panel/tarifas/iva/', views_admin.iva_guardar, name='iva_guardar'),
    path('panel/tarifas/<int:pk>/precio/', views_admin.tarifa_precio, name='tarifa_precio'),
    path('panel/tarifas/<int:pk>/eliminar/', views_admin.tarifa_eliminar, name='tarifa_eliminar'),
    path('panel/servicios/<int:pk>/precio/', views_admin.servicio_precio, name='servicio_precio'),
    path('panel/servicios/<int:pk>/eliminar/', views_admin.servicio_eliminar, name='servicio_eliminar'),
]
