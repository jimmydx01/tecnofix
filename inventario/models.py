from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

DINERO = dict(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])


class Proveedor(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    telefono = models.CharField('teléfono', max_length=20, blank=True)

    class Meta:
        verbose_name_plural = 'proveedores'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """Repuesto o producto del inventario."""

    nombre = models.CharField(max_length=120)
    codigo = models.CharField('código', max_length=30, unique=True)
    marca = models.CharField(max_length=60, blank=True)
    categoria = models.CharField('categoría', max_length=60, blank=True)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    precio_venta = models.DecimalField('costo de venta', **DINERO)
    costo_pedido = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField('stock mínimo', default=0)
    activo = models.BooleanField(default=True)
    proveedores = models.ManyToManyField(Proveedor, through='ProductoProveedor')

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.codigo})'

    @property
    def stock_bajo(self):
        return self.stock <= self.stock_minimo


class ProductoProveedor(models.Model):
    """Precio que ofrece cada proveedor por un producto. Máximo 2 proveedores por producto."""

    MAXIMO = 2

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='cotizaciones')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    precio = models.DecimalField(**DINERO)

    class Meta:
        verbose_name = 'precio de proveedor'
        verbose_name_plural = 'precios de proveedores'
        constraints = [
            models.UniqueConstraint(fields=['producto', 'proveedor'], name='un_precio_por_proveedor'),
        ]

    def __str__(self):
        return f'{self.producto.nombre} · {self.proveedor.nombre}: ${self.precio}'

    def clean(self):
        otros = ProductoProveedor.objects.filter(producto_id=self.producto_id).exclude(pk=self.pk)
        if otros.count() >= self.MAXIMO:
            raise ValidationError(f'Un producto puede tener como máximo {self.MAXIMO} proveedores.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Pedido(models.Model):
    """Reposición de stock a un proveedor."""

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unit = models.DecimalField('precio por unidad', **DINERO)
    costo_total = models.GeneratedField(
        expression=F('cantidad') * F('precio_unit'),
        output_field=models.DecimalField(max_digits=12, decimal_places=2),
        db_persist=True,
    )
    observacion = models.TextField('observación', blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f'Pedido #{self.pk}: {self.cantidad} x {self.producto.nombre}'


class MovimientoInventario(models.Model):
    """Kardex: toda entrada o salida de stock queda registrada aquí."""

    class Tipo(models.TextChoices):
        ENTRADA = 'ENTRADA', 'Entrada'
        SALIDA = 'SALIDA', 'Salida'
        AJUSTE = 'AJUSTE', 'Ajuste'

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='movimientos')
    tipo = models.CharField(max_length=8, choices=Tipo.choices)
    cantidad = models.IntegerField()
    stock_resultante = models.IntegerField()
    motivo = models.CharField(max_length=150, blank=True)
    pedido = models.ForeignKey(Pedido, on_delete=models.SET_NULL, null=True, blank=True)
    presupuesto = models.ForeignKey(
        'ordenes.Presupuesto', on_delete=models.SET_NULL, null=True, blank=True
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-fecha', '-id']
        verbose_name = 'movimiento de inventario'
        verbose_name_plural = 'movimientos de inventario'
        constraints = [
            models.CheckConstraint(condition=~Q(cantidad=0), name='movimiento_cantidad_distinta_de_cero'),
            models.CheckConstraint(
                condition=Q(tipo='AJUSTE') | Q(cantidad__gt=0), name='entrada_o_salida_positiva'
            ),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} de {self.cantidad} · {self.producto.nombre}'


class PiezaSolicitada(models.Model):
    """Pieza que el técnico necesita y no está disponible."""

    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        DISPONIBLE = 'DISPONIBLE', 'Disponible'

    orden = models.ForeignKey(
        'ordenes.Orden', on_delete=models.CASCADE, related_name='piezas_solicitadas'
    )
    tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        limit_choices_to={'rol': 'TECNICO'},
    )
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True)
    nombre_pieza = models.CharField(max_length=120)
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    observacion = models.TextField('observación', blank=True)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    creada_en = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'pieza solicitada'
        verbose_name_plural = 'piezas solicitadas'

    def __str__(self):
        return f'{self.cantidad} x {self.nombre_pieza} (orden {self.orden_id})'
