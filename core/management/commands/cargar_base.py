from django.core.management.base import BaseCommand

from core.models import Configuracion
from core.imagenes import POR_SERVICIO
from ordenes.models import Servicio, Tarifa

SERVICIOS = [
    ('Reparación de computadoras', 40),
    ('Celulares y tablets', 30),
    ('Impresoras', 35),
    ('Redes y WiFi', 45),
    ('Consolas y gaming', 50),
    ('Mantenimiento preventivo', 25),
]

TARIFAS = [
    ('Mano de obra', 20),
    ('Limpieza de equipo', 10),
    ('Diagnóstico', 5),
    ('Instalación de sistema', 15),
    ('Respaldo de datos', 12),
    ('Cambio de pantalla (mano de obra)', 25),
]


class Command(BaseCommand):
    help = 'Carga los servicios, las tarifas base y el IVA con los que arranca TecnoFix. Se puede ejecutar varias veces.'

    def handle(self, *args, **opciones):
        for nombre, precio in SERVICIOS:
            servicio, _ = Servicio.objects.get_or_create(nombre=nombre, defaults={'precio_base': precio})
            # Si el servicio todavía no tiene foto, se le pone la de ejemplo (nunca pisa una que ya elegiste)
            if not servicio.imagen and nombre in POR_SERVICIO:
                servicio.imagen = POR_SERVICIO[nombre]
                servicio.save(update_fields=['imagen'])
        for nombre, precio in TARIFAS:
            Tarifa.objects.get_or_create(nombre=nombre, defaults={'precio': precio})
        iva = Configuracion.iva()
        self.stdout.write(self.style.SUCCESS(
            f'Listo: {Servicio.objects.count()} servicios, {Tarifa.objects.count()} tarifas, IVA {iva}%.'
        ))
