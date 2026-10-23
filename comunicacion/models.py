from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Notificacion(models.Model):
    """Aviso dentro del sistema. Cada usuario solo ve las suyas."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificaciones'
    )
    texto = models.CharField(max_length=255)
    leida = models.BooleanField(default=False)
    creada_en = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-creada_en']
        verbose_name = 'notificación'
        verbose_name_plural = 'notificaciones'
        indexes = [models.Index(fields=['usuario', 'leida'])]

    def __str__(self):
        return f'{self.usuario.nombre}: {self.texto[:50]}'

    @classmethod
    def avisar(cls, usuario, texto):
        """Atajo para crear una notificación (no hace nada si no hay usuario)."""
        if usuario:
            return cls.objects.create(usuario=usuario, texto=texto)


class Mensaje(models.Model):
    """Mensaje del chat interno entre cliente, técnico y administrador."""

    orden = models.ForeignKey(
        'ordenes.Orden', on_delete=models.CASCADE, null=True, blank=True, related_name='mensajes'
    )
    de = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mensajes_enviados'
    )
    para = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mensajes_recibidos'
    )
    texto = models.TextField()
    leido = models.BooleanField(default=False)
    creado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['creado_en']
        constraints = [
            models.CheckConstraint(condition=~Q(de=F('para')), name='mensaje_no_a_uno_mismo'),
        ]

    def __str__(self):
        return f'{self.de.nombre} a {self.para.nombre}: {self.texto[:40]}'
