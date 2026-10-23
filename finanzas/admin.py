from django.contrib import admin

from .models import Gasto


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'tipo', 'concepto', 'monto')
    list_filter = ('tipo',)
    search_fields = ('concepto',)
