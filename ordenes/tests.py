from decimal import Decimal

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from core.models import Configuracion
from usuarios.models import Usuario

from .models import Orden, Servicio, Tarifa

CLAVE = 'Taller-2026-ok'


class TarifasBase(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser('admin@correo.com', 'Admin Uno', CLAVE)
        self.cliente = Usuario.objects.create_user('c@correo.com', 'Cli Uno', CLAVE, rol='CLIENTE')
        self.client.force_login(self.admin)

    def mensajes(self, r):
        return [str(m) for m in get_messages(r.wsgi_request)]


class PermisosTarifas(TarifasBase):
    def test_solo_el_admin_entra_y_actua(self):
        t = Tarifa.objects.create(nombre='Limpieza', precio=10)
        urls = [reverse('tarifas')]
        posts = [reverse('iva_guardar'), reverse('tarifa_precio', args=[t.pk]), reverse('tarifa_eliminar', args=[t.pk])]
        self.client.force_login(self.cliente)
        for u in urls:
            self.assertEqual(self.client.get(u).status_code, 302)
        for u in posts:
            self.assertEqual(self.client.post(u, {'valor': '5', 'precio': '1'}).status_code, 302)
        self.assertTrue(Tarifa.objects.filter(pk=t.pk, precio=10).exists())
        self.assertNotEqual(Configuracion.iva(), Decimal('5'))
        self.client.logout()
        self.assertEqual(self.client.get(urls[0]).status_code, 302)

    def test_acciones_solo_post(self):
        t = Tarifa.objects.create(nombre='Limpieza', precio=10)
        self.assertEqual(self.client.get(reverse('tarifa_eliminar', args=[t.pk])).status_code, 405)

    def test_pestana_visible(self):
        self.assertContains(self.client.get(reverse('tarifas')), 'Impuesto (IVA)')


class IvaTests(TarifasBase):
    def test_guardar_iva(self):
        self.client.post(reverse('iva_guardar'), {'valor': '12.5'})
        self.assertEqual(Configuracion.iva(), Decimal('12.5'))

    def test_iva_cero_es_valido(self):
        self.client.post(reverse('iva_guardar'), {'valor': '0'})
        self.assertEqual(Configuracion.iva(), Decimal('0'))

    def test_iva_invalido(self):
        Configuracion.iva()
        for malo in ('-1', '101', 'abc', ''):
            r = self.client.post(reverse('iva_guardar'), {'valor': malo})
            self.assertTrue(self.mensajes(r), malo)
        self.assertEqual(Configuracion.iva(), Decimal('15'))


class TarifaTests(TarifasBase):
    def alta(self, **c):
        return self.client.post(reverse('tarifas'), {'accion': 'tarifa', 'nombre': 'Mano de obra', 'precio': '20', **c})

    def test_alta(self):
        self.assertRedirects(self.alta(), reverse('tarifas'))
        self.assertEqual(Tarifa.objects.get().precio, Decimal('20'))

    def test_validaciones(self):
        for datos in ({'precio': '0'}, {'precio': '-3'}, {'precio': 'x'}, {'precio': ''}, {'nombre': ''}, {'nombre': 'ab'}, {'precio': '1.234'}):
            r = self.alta(**datos)
            self.assertEqual(r.status_code, 200, datos)
        self.assertEqual(Tarifa.objects.count(), 0)

    def test_nombre_repetido_sin_distinguir_mayusculas(self):
        self.alta()
        r = self.alta(nombre='mano de OBRA')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Tarifa.objects.count(), 1)

    def test_cambiar_precio(self):
        t = Tarifa.objects.create(nombre='Limpieza', precio=10)
        self.client.post(reverse('tarifa_precio', args=[t.pk]), {'precio': '12.75'})
        t.refresh_from_db()
        self.assertEqual(t.precio, Decimal('12.75'))

    def test_precio_invalido_no_cambia(self):
        t = Tarifa.objects.create(nombre='Limpieza', precio=10)
        for malo in ('0', '-1', 'abc', ''):
            self.client.post(reverse('tarifa_precio', args=[t.pk]), {'precio': malo})
        t.refresh_from_db()
        self.assertEqual(t.precio, Decimal('10'))

    def test_eliminar(self):
        t = Tarifa.objects.create(nombre='Limpieza', precio=10)
        self.client.post(reverse('tarifa_eliminar', args=[t.pk]))
        self.assertFalse(Tarifa.objects.exists())

    def test_la_pantalla_muestra_numeros_con_punto(self):
        Tarifa.objects.create(nombre='Limpieza', precio=Decimal('12.50'))
        self.assertContains(self.client.get(reverse('tarifas')), 'value="12.5"')


class ServicioTests(TarifasBase):
    def alta(self, **c):
        return self.client.post(reverse('tarifas'), {'accion': 'servicio', 'imagen': 'https://ejemplo.com/tv.jpg', 'nombre': 'Televisores', 'precio_base': '30', **c})

    def test_alta(self):
        self.assertRedirects(self.alta(), reverse('tarifas'))
        s = Servicio.objects.get()
        self.assertEqual((s.imagen, s.precio_base), ('https://ejemplo.com/tv.jpg', Decimal('30')))

    def test_la_imagen_es_opcional(self):
        self.alta(imagen='')
        self.assertEqual(Servicio.objects.get().imagen, '')

    def test_imagen_con_vinculo_invalido(self):
        for malo in ('foto.jpg', 'javascript:alert(1)', 'ftp://x.com/a.jpg'):
            self.assertEqual(self.alta(imagen=malo).status_code, 200, malo)
        self.assertEqual(Servicio.objects.count(), 0)

    def test_validaciones(self):
        for datos in ({'precio_base': '0'}, {'precio_base': 'x'}, {'nombre': ''}, {'nombre': 'ab'}):
            self.assertEqual(self.alta(**datos).status_code, 200, datos)
        self.assertEqual(Servicio.objects.count(), 0)

    def test_nombre_repetido(self):
        self.alta()
        self.assertEqual(self.alta(nombre='televisores').status_code, 200)
        self.assertEqual(Servicio.objects.count(), 1)

    def test_cambiar_precio_base(self):
        s = Servicio.objects.create(nombre='Laptops', precio_base=40)
        self.client.post(reverse('servicio_precio', args=[s.pk]), {'precio': '45'})
        s.refresh_from_db()
        self.assertEqual(s.precio_base, Decimal('45'))

    def test_eliminar_libre_y_bloqueado_con_ordenes(self):
        libre = Servicio.objects.create(nombre='Libre', precio_base=5)
        usado = Servicio.objects.create(nombre='Usado', precio_base=5)
        Orden.objects.create(cliente=self.cliente, servicio=usado, modelo='HP')
        self.client.post(reverse('servicio_eliminar', args=[libre.pk]))
        r = self.client.post(reverse('servicio_eliminar', args=[usado.pk]))
        self.assertFalse(Servicio.objects.filter(pk=libre.pk).exists())
        self.assertTrue(Servicio.objects.filter(pk=usado.pk).exists())
        self.assertIn('no se puede eliminar', ' '.join(self.mensajes(r)))
