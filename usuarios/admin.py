from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import UsuarioChangeForm, UsuarioCreationForm
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    form = UsuarioChangeForm
    add_form = UsuarioCreationForm
    list_display = ('nombre', 'email', 'rol', 'telefono', 'is_active')
    list_filter = ('rol', 'is_active')
    search_fields = ('nombre', 'email')
    ordering = ('nombre',)
    filter_horizontal = ('groups', 'user_permissions')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Datos personales', {'fields': ('nombre', 'telefono', 'rol', 'acepto_datos_en')}),
        ('Permisos', {'fields': ('is_active', 'debe_cambiar_contrasena', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('last_login', 'creado_en')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'nombre', 'telefono', 'rol', 'password1', 'password2')}),
    )
