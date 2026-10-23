from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Gasto(models.Model):
    """Gasto o pérdida del negocio. Los pedidos a proveedores crean su gasto automáticamente."""

    class Tipo(models.TextChoices):
        GASTO = 'GASTO', 'Gasto'
        PERDIDA = 'PERDIDA', 'Pérdida'

    tipo = models.CharField(max_length=8, choices=Tipo.choices, default=Tipo.GASTO)
    concepto = models.CharField(max_length=150)
    monto = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))]
    )
    fecha = models.DateField(default=timezone.localdate)
    pedido = models.OneToOneField(
        'inventario.Pedido', on_delete=models.SET_NULL, null=True, blank=True
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ['-fecha']
        constraints = [models.CheckConstraint(condition=Q(monto__gt=0), name='gasto_monto_positivo')]

    def __str__(self):
        return f'{self.get_tipo_display()}: {self.concepto} (${self.monto})'
