from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ordenes.models import Orden, Servicio, Tarifa
from .imagenes import PORTADA
from usuarios.forms import IngresoForm, RegistroForm


def contexto_inicio(**extra):
    """Todo lo que necesita la página principal. Las vistas de ingreso y registro la reutilizan."""
    servicios = Servicio.objects.all()
    entregadas = Orden.objects.filter(estado=Orden.Estado.ENTREGADO).count()
    contexto = {
        'servicios': servicios,
        'portada': {'imagen': PORTADA, 'nombre': 'portada'},
        'tarifas': Tarifa.objects.all(),
        # Las tres tarjetas de colores se calculan con datos reales de la base
        'estadisticas': [
            (entregadas, 'equipos reparados', 'g1'),
            (Orden.objects.count() - entregadas, 'equipos en proceso', 'g2'),
            (servicios.count(), 'servicios disponibles', 'g3'),
        ],
        'form_ingreso': IngresoForm(auto_id='ing_%s'),
        'form_registro': RegistroForm(auto_id='reg_%s'),
        'modal_abierto': None,
        'siguiente': '',
    }
    contexto.update(extra)
    return contexto


def inicio(request):
    """Página principal: presentación, servicios y precios base."""
    return render(request, 'core/inicio.html', contexto_inicio())


@login_required
def panel(request):
    """Panel de inicio según el rol. El administrador ve su panel con pestañas."""
    usuario = request.user
    activas = Orden.objects.exclude(estado=Orden.Estado.ENTREGADO)
    if usuario.es_cliente:
        activas = activas.filter(cliente=usuario)
    elif usuario.es_tecnico:
        activas = activas.filter(tecnico=usuario)
    plantilla = 'panel/dashboard_admin.html' if usuario.es_admin else 'core/panel.html'
    return render(request, plantilla, {'en_proceso': activas.count(), 'tab': 'dash'})
