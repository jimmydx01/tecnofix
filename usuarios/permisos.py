from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def solo_admin(vista):
    """La vista solo la puede usar quien ingresó con rol de administrador."""

    @wraps(vista)
    @login_required
    def envoltura(request, *args, **kwargs):
        if not request.user.es_admin:
            messages.error(request, 'No tienes permiso para entrar a esa sección.')
            return redirect('panel')
        return vista(request, *args, **kwargs)

    return envoltura
