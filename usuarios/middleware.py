from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class ExigirCambioContrasena:
    """Si el administrador asignó una contraseña temporal, solo se puede cambiarla o salir."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = request.user
        if usuario.is_authenticated and usuario.debe_cambiar_contrasena:
            permitidas = {reverse('cambiar_contrasena'), reverse('salir')}
            es_archivo = request.path.startswith((settings.STATIC_URL, settings.MEDIA_URL))
            if request.path not in permitidas and not es_archivo:
                messages.warning(request, 'Por seguridad, cambia tu contraseña temporal para continuar.')
                return redirect('cambiar_contrasena')
        return self.get_response(request)
