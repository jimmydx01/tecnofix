from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .models import Usuario

CLAVE = 'Taller-2026-ok'
NUEVA = 'Otra-Clave-2026'


class CambioContrasenaTests(TestCase):
    def setUp(self):
        cache.clear()
        self.u = Usuario.objects.create_user('ana@correo.com', 'Ana Pérez', CLAVE, rol='CLIENTE')
        self.admin = Usuario.objects.create_superuser('admin@correo.com', 'Admin Uno', CLAVE)
        self.client.force_login(self.u)

    def cambiar(self, actual=CLAVE, nueva=NUEVA, repetir=None):
        return self.client.post(reverse('cambiar_contrasena'),
                                {'actual': actual, 'nueva': nueva, 'repetir': repetir or nueva})

    def test_exige_ingresar(self):
        self.client.logout()
        r = self.client.get(reverse('cambiar_contrasena'))
        self.assertEqual(r.status_code, 302)

    def test_cambio_correcto_y_la_sesion_se_mantiene(self):
        r = self.cambiar()
        self.assertEqual(r.status_code, 302)
        self.u.refresh_from_db()
        self.assertTrue(self.u.check_password(NUEVA))
        self.assertEqual(self.client.get(reverse('panel')).status_code, 200)

    def test_actual_incorrecta(self):
        r = self.cambiar(actual='Equivocada-123')
        self.assertEqual(r.status_code, 200)
        self.u.refresh_from_db()
        self.assertTrue(self.u.check_password(CLAVE))

    def test_no_coinciden(self):
        r = self.cambiar(repetir='Distinta-2026-x')
        self.assertEqual(r.status_code, 200)
        self.u.refresh_from_db()
        self.assertTrue(self.u.check_password(CLAVE))

    def test_nueva_igual_a_actual(self):
        r = self.cambiar(nueva=CLAVE)
        self.assertEqual(r.status_code, 200)

    def test_validadores(self):
        for mala in ('12345678', 'corta1', 'password'):
            r = self.cambiar(nueva=mala)
            self.assertEqual(r.status_code, 200, mala)
        self.u.refresh_from_db()
        self.assertTrue(self.u.check_password(CLAVE))

    def test_bloqueo_tras_intentos_fallidos(self):
        for _ in range(6):
            self.cambiar(actual='Equivocada-123')
        r = self.cambiar()  # ahora con la clave correcta
        self.u.refresh_from_db()
        self.assertTrue(self.u.check_password(CLAVE))
        self.assertEqual(r.status_code, 200)


class CambioObligatorioTests(TestCase):
    def setUp(self):
        self.u = Usuario.objects.create_user('t@correo.com', 'Tec Uno', CLAVE, rol='TECNICO',
                                             debe_cambiar_contrasena=True)
        self.client.force_login(self.u)

    def test_todo_redirige_a_cambiar(self):
        for nombre in ('panel', 'inicio'):
            r = self.client.get(reverse(nombre))
            self.assertRedirects(r, reverse('cambiar_contrasena'), fetch_redirect_response=False)

    def test_puede_ver_la_pantalla_y_salir(self):
        self.assertEqual(self.client.get(reverse('cambiar_contrasena')).status_code, 200)
        self.assertEqual(self.client.post(reverse('salir')).status_code, 302)

    def test_al_cambiar_queda_libre(self):
        self.client.post(reverse('cambiar_contrasena'), {'actual': CLAVE, 'nueva': NUEVA, 'repetir': NUEVA})
        self.u.refresh_from_db()
        self.assertFalse(self.u.debe_cambiar_contrasena)
        self.assertEqual(self.client.get(reverse('panel')).status_code, 200)


class RestablecerTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser('admin@correo.com', 'Admin Uno', CLAVE)
        self.t = Usuario.objects.create_user('t@correo.com', 'Tec Uno', CLAVE, rol='TECNICO')

    def url(self, u=None):
        return reverse('usuario_contrasena', args=[(u or self.t).pk])

    def test_admin_restablece_y_obliga_a_cambiar(self):
        self.client.force_login(self.admin)
        r = self.client.post(self.url(), {'password': 'Temporal-2026-z'})
        self.assertEqual(r.status_code, 302)
        self.t.refresh_from_db()
        self.assertTrue(self.t.check_password('Temporal-2026-z'))
        self.assertTrue(self.t.debe_cambiar_contrasena)

    def test_clave_temporal_debil_se_rechaza(self):
        self.client.force_login(self.admin)
        r = self.client.post(self.url(), {'password': '12345678'})
        self.assertEqual(r.status_code, 200)
        self.t.refresh_from_db()
        self.assertTrue(self.t.check_password(CLAVE))

    def test_no_aplica_a_administradores(self):
        self.client.force_login(self.admin)
        otro = Usuario.objects.create_superuser('otro@correo.com', 'Otro Admin', CLAVE)
        r = self.client.post(self.url(otro), {'password': 'Temporal-2026-z'})
        self.assertEqual(r.status_code, 404)

    def test_solo_admin(self):
        self.client.force_login(self.t)
        self.assertIn(self.client.get(self.url()).status_code, (302, 403, 404))
        self.client.logout()
        self.assertEqual(self.client.get(self.url()).status_code, 302)
