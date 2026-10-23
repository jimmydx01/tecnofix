from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

DINERO = dict(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])


class Servicio(models.Model):
    imagen = models.URLField('imagen (vínculo)', max_length=500, blank=True, help_text='Vínculo de una foto del servicio. Si se deja vacío o falla, se muestra un ícono.')
    nombre = models.CharField(max_length=100, unique=True)
    precio_base = models.DecimalField(**DINERO)

    class Meta:
        verbose_name_plural = 'servicios'
        ordering = ['id']

    def __str__(self):
        return self.nombre


class Tarifa(models.Model):
    """Tarifa base: mano de obra, limpieza de equipo, etc."""

    nombre = models.CharField(max_length=100, unique=True)
    precio = models.DecimalField(**DINERO)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.nombre} (${self.precio})'


class Orden(models.Model):
    """Solicitud de servicio de un cliente sobre un equipo."""

    class Estado(models.TextChoices):
        RECIBIDO = 'RECIBIDO', 'Recibido'
        DIAGNOSTICO = 'DIAGNOSTICO', 'En diagnóstico'
        REPARACION = 'REPARACION', 'En reparación'
        LISTO = 'LISTO', 'Listo'
        ENTREGADO = 'ENTREGADO', 'Entregado'

    class Prioridad(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal'
        ALTA = 'ALTA', 'Alta'
        URGENTE = 'URGENTE', 'Urgente'

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ordenes_como_cliente',
        limit_choices_to={'rol': 'CLIENTE'},
    )
    tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordenes_como_tecnico',
        limit_choices_to={'rol': 'TECNICO'},
    )
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT)
    modelo = models.CharField('modelo del equipo', max_length=100)
    problema = models.TextField(blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.RECIBIDO)
    prioridad = models.CharField(max_length=8, choices=Prioridad.choices, default=Prioridad.NORMAL)
    fecha_estimada = models.DateField('fecha estimada de entrega', null=True, blank=True)
    espera_repuesto = models.BooleanField(default=False)
    entrega_autorizada = models.BooleanField(default=False)
    creada_en = models.DateTimeField(default=timezone.now)
    entregada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creada_en']
        verbose_name = 'orden'
        constraints = [
            models.CheckConstraint(
                condition=~Q(estado='ENTREGADO') | Q(entrega_autorizada=True),
                name='entregada_requiere_autorizacion',
            ),
            models.CheckConstraint(
                condition=Q(estado='ENTREGADO', entregada_en__isnull=False)
                | (~Q(estado='ENTREGADO') & Q(entregada_en__isnull=True)),
                name='fecha_de_entrega_solo_si_entregada',
            ),
        ]

    def __str__(self):
        return f'Orden #{self.pk} · {self.modelo}'

    @property
    def presupuesto_aceptado(self):
        return self.presupuestos.filter(estado=Presupuesto.Estado.ACEPTADO).first()

    @property
    def atrasada(self):
        """Pasó la fecha estimada y todavía no se entrega."""
        return bool(
            self.fecha_estimada
            and self.estado != self.Estado.ENTREGADO
            and self.fecha_estimada < timezone.localdate()
        )


class OrdenFoto(models.Model):
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='fotos')
    imagen = models.ImageField(upload_to='ordenes/%Y/%m/')

    class Meta:
        verbose_name = 'foto de la orden'
        verbose_name_plural = 'fotos de la orden'


class HistorialOrden(models.Model):
    """Cada cambio de una orden, con fecha y responsable."""

    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='historial')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    evento = models.CharField(max_length=200)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'historial de la orden'
        verbose_name_plural = 'historial de órdenes'

    def __str__(self):
        return f'{self.evento} ({self.fecha:%d/%m/%Y %H:%M})'


class Presupuesto(models.Model):
    """Cotización que el técnico envía al cliente."""

    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        ACEPTADO = 'ACEPTADO', 'Aceptado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'

    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='presupuestos')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    iva_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    observacion = models.TextField('observación', blank=True)
    creado_en = models.DateTimeField(default=timezone.now)
    respondido_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creado_en']
        constraints = [
            models.CheckConstraint(condition=Q(total=F('subtotal') + F('iva')), name='total_es_subtotal_mas_iva'),
            models.UniqueConstraint(
                fields=['orden'], condition=Q(estado='ACEPTADO'), name='un_presupuesto_aceptado_por_orden'
            ),
            models.UniqueConstraint(
                fields=['orden'], condition=Q(estado='PENDIENTE'), name='un_presupuesto_pendiente_por_orden'
            ),
        ]

    def __str__(self):
        return f'Presupuesto #{self.pk} de la orden {self.orden_id}'


class PresupuestoItem(models.Model):
    """Línea del presupuesto: una tarifa (servicio) o un repuesto del inventario."""

    class Tipo(models.TextChoices):
        SERVICIO = 'SERVICIO', 'Servicio'
        REPUESTO = 'REPUESTO', 'Repuesto'

    presupuesto = models.ForeignKey(Presupuesto, on_delete=models.CASCADE, related_name='items')
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    tarifa = models.ForeignKey(Tarifa, on_delete=models.PROTECT, null=True, blank=True)
    producto = models.ForeignKey(
        'inventario.Producto', on_delete=models.PROTECT, null=True, blank=True
    )
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    precio_unit = models.DecimalField('precio por unidad', max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'línea del presupuesto'
        verbose_name_plural = 'líneas del presupuesto'
        constraints = [
            models.CheckConstraint(
                condition=Q(tipo='SERVICIO', tarifa__isnull=False, producto__isnull=True)
                | Q(tipo='REPUESTO', producto__isnull=False, tarifa__isnull=True),
                name='linea_servicio_o_repuesto',
            ),
        ]

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unit

    def save(self, *args, **kwargs):
        # Copia el precio vigente, para que un cambio posterior no altere presupuestos viejos.
        if not self.precio_unit:
            if self.tipo == self.Tipo.SERVICIO and self.tarifa:
                self.precio_unit = self.tarifa.precio
            elif self.tipo == self.Tipo.REPUESTO and self.producto:
                self.precio_unit = self.producto.precio_venta
        super().save(*args, **kwargs)


class Pago(models.Model):
    """Pago en efectivo o por transferencia. La transferencia lleva comprobante y lo valida el administrador."""

    class Metodo(models.TextChoices):
        EFECTIVO = 'EFECTIVO', 'Efectivo'
        TRANSFERENCIA = 'TRANSFERENCIA', 'Transferencia'

    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente de validar'
        CONFIRMADO = 'CONFIRMADO', 'Confirmado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'

    orden = models.ForeignKey(Orden, on_delete=models.PROTECT, related_name='pagos')
    metodo = models.CharField(max_length=14, choices=Metodo.choices)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    comprobante = models.FileField(upload_to='comprobantes/%Y/%m/', blank=True)
    referencia = models.CharField(max_length=60, blank=True)
    motivo_rechazo = models.TextField(blank=True)
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagos_validados',
        limit_choices_to={'rol': 'ADMIN'},
    )
    validado_en = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-creado_en']
        constraints = [
            models.CheckConstraint(condition=Q(monto__gt=0), name='pago_monto_positivo'),
            models.CheckConstraint(
                condition=~Q(metodo='TRANSFERENCIA') | ~Q(comprobante=''),
                name='transferencia_requiere_comprobante',
            ),
            models.CheckConstraint(
                condition=Q(estado='PENDIENTE') | (Q(validado_por__isnull=False) & Q(validado_en__isnull=False)),
                name='pago_validado_tiene_responsable',
            ),
            models.CheckConstraint(
                condition=~Q(estado='RECHAZADO') | ~Q(motivo_rechazo=''),
                name='rechazo_requiere_motivo',
            ),
            models.UniqueConstraint(
                fields=['orden'], condition=Q(estado='CONFIRMADO'), name='un_pago_confirmado_por_orden'
            ),
            models.UniqueConstraint(
                fields=['orden'], condition=Q(estado='PENDIENTE'), name='un_pago_pendiente_por_orden'
            ),
        ]

    def __str__(self):
        return f'Pago {self.get_metodo_display()} de ${self.monto} (orden {self.orden_id})'
