"""Tarifas, servicios e IVA que configura el administrador."""

from django.contrib import messages
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.models import Configuracion
from usuarios.permisos import solo_admin

from .forms import IvaForm, PrecioForm, ServicioForm, TarifaForm
from .models import Servicio, Tarifa


def _primer_error(form):
    for errores in form.errors.values():
        return errores[0]
    return 'Datos no válidos.'


@solo_admin
def tarifas(request):
    form_tarifa = TarifaForm(auto_id='tar_%s')
    form_servicio = ServicioForm(auto_id='srv_%s')
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'tarifa':
            form_tarifa = TarifaForm(request.POST, auto_id='tar_%s')
            if form_tarifa.is_valid():
                form_tarifa.save()
                messages.success(request, 'Tarifa añadida')
                return redirect('tarifas')
        elif accion == 'servicio':
            form_servicio = ServicioForm(request.POST, auto_id='srv_%s')
            if form_servicio.is_valid():
                form_servicio.save()
                messages.success(request, 'Servicio añadido')
                return redirect('tarifas')
    return render(request, 'panel/tarifas.html', {
        'tab': 'tar',
        'iva': Configuracion.iva(),
        'tarifas': Tarifa.objects.all(),
        'servicios': Servicio.objects.all(),
        'form_tarifa': form_tarifa,
        'form_servicio': form_servicio,
    })


@solo_admin
@require_POST
def iva_guardar(request):
    form = IvaForm(request.POST)
    if form.is_valid():
        Configuracion.objects.update_or_create(
            clave=Configuracion.IVA,
            defaults={'valor': form.cleaned_data['valor'], 'descripcion': 'Porcentaje de IVA que se suma a los presupuestos'},
        )
        messages.success(request, f'IVA actualizado a {form.cleaned_data["valor"].normalize():f}%')
    else:
        messages.error(request, _primer_error(form))
    return redirect('tarifas')


@solo_admin
@require_POST
def tarifa_precio(request, pk):
    tarifa = get_object_or_404(Tarifa, pk=pk)
    form = PrecioForm(request.POST)
    if form.is_valid():
        tarifa.precio = form.cleaned_data['precio']
        tarifa.save(update_fields=['precio'])
        messages.success(request, f'Precio de «{tarifa.nombre}» actualizado')
    else:
        messages.error(request, _primer_error(form))
    return redirect('tarifas')


@solo_admin
@require_POST
def tarifa_eliminar(request, pk):
    tarifa = get_object_or_404(Tarifa, pk=pk)
    try:
        with transaction.atomic():
            tarifa.delete()
    except ProtectedError:
        messages.error(request, f'«{tarifa.nombre}» ya se usó en presupuestos y no se puede eliminar.')
    else:
        messages.success(request, 'Tarifa eliminada')
    return redirect('tarifas')


@solo_admin
@require_POST
def servicio_precio(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    form = PrecioForm(request.POST)
    if form.is_valid():
        servicio.precio_base = form.cleaned_data['precio']
        servicio.save(update_fields=['precio_base'])
        messages.success(request, f'Precio de «{servicio.nombre}» actualizado')
    else:
        messages.error(request, _primer_error(form))
    return redirect('tarifas')


@solo_admin
@require_POST
def servicio_eliminar(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    try:
        with transaction.atomic():
            servicio.delete()
    except ProtectedError:
        messages.error(request, f'«{servicio.nombre}» tiene órdenes registradas y no se puede eliminar.')
    else:
        messages.success(request, 'Servicio eliminado')
    return redirect('tarifas')
