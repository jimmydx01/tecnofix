from django.contrib import admin

from .models import Mensaje, Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'texto', 'leida', 'creada_en')
    list_filter = ('leida',)


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ('de', 'para', 'orden', 'texto', 'leido', 'creado_en')
    list_filter = ('leido',)
