from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from ordenes.models import Servicio, Tarifa
from usuarios.models import Usuario


class PaginaPrincipalTests(TestCase):
    def test_carga_sin_datos(self):
        r = self.client.get(reverse('inicio'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Tu tecnología,')
        self.assertContains(r, 'Aún no hay servicios')

    def test_muestra_servicios_y_tarifas_desde_la_base(self):
        Servicio.objects.create(nombre='Reparación de computadoras', precio_base=40)
        Tarifa.objects.create(nombre='Mano de obra', precio=20)
        r = self.client.get(reverse('inicio'))
        self.assertContains(r, 'Reparación de computadoras')
        self.assertContains(r, '$40.00')
        self.assertContains(r, 'Mano de obra')
        self.assertContains(r, '$20.00')

    def test_cargar_base_se_puede_repetir(self):
        call_command('cargar_base', stdout=StringIO())
        call_command('cargar_base', stdout=StringIO())
        self.assertEqual(Servicio.objects.count(), 6)
        self.assertEqual(Tarifa.objects.count(), 6)

    def test_salir_cierra_la_sesion(self):
        usuario = Usuario.objects.create_user('a@b.com', 'Ana', 'Clave12345')
        self.client.force_login(usuario)
        r = self.client.post(reverse('salir'))
        self.assertRedirects(r, reverse('inicio'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_menu_con_sesion_iniciada(self):
        usuario = Usuario.objects.create_user('b@c.com', 'Beto Prueba', 'Clave12345')
        self.client.force_login(usuario)
        r = self.client.get(reverse('inicio'))
        self.assertContains(r, 'Beto Prueba')
        self.assertContains(r, 'Salir')
        self.assertNotContains(r, 'modal-ingresar')
