from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('panel/', views.panel, name='panel'),
    path('salir/', LogoutView.as_view(next_page='inicio'), name='salir'),
]
