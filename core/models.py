from decimal import Decimal

from django.db import models


class Configuracion(models.Model):
    """Parámetros del sistema que puede cambiar el administrador (por ejemplo, el IVA)."""

    IVA = 'IVA_PORCENTAJE'

    clave = models.CharField(max_length=50, primary_key=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'configuración'
        verbose_name_plural = 'configuraciones'

    def __str__(self):
        return f'{self.clave} = {self.valor}'

    @classmethod
    def iva(cls):
        """Porcentaje de IVA vigente. Si no existe todavía, se crea con 15."""
        parametro, _ = cls.objects.get_or_create(
            clave=cls.IVA,
            defaults={'valor': Decimal('15'), 'descripcion': 'Porcentaje de IVA que se suma a los presupuestos'},
        )
        return parametro.valor
