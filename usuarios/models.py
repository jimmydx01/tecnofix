from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UsuarioManager


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Persona que usa el sistema. El rol define qué puede ver y hacer."""

    class Rol(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        TECNICO = 'TECNICO', 'Técnico'
        CLIENTE = 'CLIENTE', 'Cliente'

    email = models.EmailField('correo', max_length=120, unique=True)
    nombre = models.CharField(max_length=100)
    telefono = models.CharField('teléfono', max_length=20, blank=True)
    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.CLIENTE)
    acepto_datos_en = models.DateTimeField('aceptó el tratamiento de datos', null=True, blank=True)
    debe_cambiar_contrasena = models.BooleanField(
        'debe cambiar la contraseña', default=False,
        help_text='Se activa cuando el administrador asigna una contraseña temporal',
    )
    is_active = models.BooleanField('activo', default=True)
    is_staff = models.BooleanField('acceso al panel de Django', default=False)
    creado_en = models.DateTimeField(default=timezone.now)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.get_rol_display()})'

    def save(self, *args, **kwargs):
        # El correo se guarda siempre en minúsculas para que no se repita con otras mayúsculas.
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    @property
    def es_admin(self):
        return self.rol == self.Rol.ADMIN

    @property
    def es_tecnico(self):
        return self.rol == self.Rol.TECNICO

    @property
    def es_cliente(self):
        return self.rol == self.Rol.CLIENTE
