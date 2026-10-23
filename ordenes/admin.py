from django.contrib import admin

from .models import (
    HistorialOrden, Orden, OrdenFoto, Pago, Presupuesto, PresupuestoItem, Servicio, Tarifa,
)


class FotoInline(admin.TabularInline):
    model = OrdenFoto
    extra = 1


class HistorialInline(admin.TabularInline):
    model = HistorialOrden
    extra = 0


@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display = ('id', 'modelo', 'cliente', 'tecnico', 'servicio', 'estado', 'prioridad', 'fecha_estimada', 'espera_repuesto')
    list_filter = ('estado', 'prioridad', 'servicio', 'espera_repuesto')
    search_fields = ('modelo', 'cliente__nombre', 'cliente__email')
    inlines = [FotoInline, HistorialInline]


class ItemInline(admin.TabularInline):
    model = PresupuestoItem
    extra = 1


@admin.register(Presupuesto)
class PresupuestoAdmin(admin.ModelAdmin):
    list_display = ('id', 'orden', 'subtotal', 'iva', 'total', 'estado', 'creado_en')
    list_filter = ('estado',)
    inlines = [ItemInline]


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'orden', 'metodo', 'monto', 'estado', 'creado_en')
    list_filter = ('metodo', 'estado')


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_base')
    list_display_links = ('nombre',)


@admin.register(Tarifa)
class TarifaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio')
