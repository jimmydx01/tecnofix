from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .models import Usuario

REGISTRO_VALIDO = {
    'nombre': 'Ana Pérez',
    'email': 'ana@correo.com',
    'telefono': '0991234567',
    'password': 'Taller-2026-ok',
    'acepto': 'on',
}


class RegistroTests(TestCase):
    def registrar(self, **cambios):
        datos = {**REGISTRO_VALIDO, **cambios}
        return self.client.post(reverse('registro'), datos)

    def test_registro_correcto_crea_cliente_y_abre_sesion(self):
        r = self.registrar()
        self.assertRedirects(r, reverse('panel'))
        u = Usuario.objects.get(email='ana@correo.com')
        self.assertEqual(u.rol, Usuario.Rol.CLIENTE)
        self.assertIsNotNone(u.acepto_datos_en)
        self.assertEqual(self.client.session['_auth_user_id'], str(u.pk))

    def test_la_contrasena_se_guarda_cifrada(self):
        self.registrar()
        u = Usuario.objects.get(email='ana@correo.com')
        self.assertNotEqual(u.password, REGISTRO_VALIDO['password'])
        self.assertTrue(u.password.startswith('pbkdf2_'))
        self.assertTrue(u.check_password(REGISTRO_VALIDO['password']))

    def test_nadie_puede_elegir_su_rol_al_registrarse(self):
        self.registrar(rol='ADMIN', is_staff='on', is_superuser='on')
        u = Usuario.objects.get(email='ana@correo.com')
        self.assertEqual(u.rol, Usuario.Rol.CLIENTE)
        self.assertFalse(u.is_staff)
        self.assertFalse(u.is_superuser)

    def test_correo_repetido_sin_importar_mayusculas(self):
        Usuario.objects.create_user('ana@correo.com', 'Otra Ana', 'Clave-segura-9')
        r = self.registrar(email='ANA@Correo.com')
        self.assertContains(r, 'ya está registrado')
        self.assertEqual(Usuario.objects.count(), 1)

    def test_correo_invalido(self):
        self.assertContains(self.registrar(email='ana@'), 'correo válido')

    def test_contrasena_debil_o_numerica_se_rechaza(self):
        for clave in ('12345678', 'abc', 'password'):
            r = self.registrar(password=clave)
            self.assertEqual(Usuario.objects.count(), 0, clave)
            self.assertEqual(r.status_code, 200)

    def test_contrasena_parecida_al_correo_se_rechaza(self):
        self.registrar(email='jimmy.martinez@correo.com', password='jimmy.martinez')
        self.assertEqual(Usuario.objects.count(), 0)

    def test_telefono_se_valida_y_se_normaliza(self):
        self.assertContains(self.registrar(telefono='12345'), 'teléfono válido')
        self.registrar(telefono='+593 99 123 4567')
        self.assertEqual(Usuario.objects.get().telefono, '0991234567')

    def test_nombre_con_numeros_o_muy_corto(self):
        self.assertContains(self.registrar(nombre='Ana123'), 'solo puede tener letras')
        self.assertContains(self.registrar(nombre='A'), 'nombre completo')

    def test_sin_aceptar_el_tratamiento_de_datos(self):
        datos = {k: v for k, v in REGISTRO_VALIDO.items() if k != 'acepto'}
        r = self.client.post(reverse('registro'), datos)
        self.assertContains(r, 'Debes aceptar')
        self.assertEqual(Usuario.objects.count(), 0)

    def test_el_error_conserva_lo_escrito_pero_nunca_la_contrasena(self):
        r = self.registrar(telefono='12345')
        self.assertContains(r, 'ana@correo.com')
        self.assertNotContains(r, REGISTRO_VALIDO['password'])

    def test_abre_la_ventana_de_registro_si_hay_errores(self):
        r = self.registrar(telefono='12345')
        self.assertEqual(r.context['modal_abierto'], 'modal-registro')


class IngresoTests(TestCase):
    def setUp(self):
        cache.clear()
        self.usuario = Usuario.objects.create_user('beto@correo.com', 'Beto Ríos', 'Taller-2026-ok')

    def ingresar(self, email='beto@correo.com', password='Taller-2026-ok', **extra):
        return self.client.post(reverse('ingresar'), {'email': email, 'password': password, **extra})

    def test_ingreso_correcto(self):
        self.assertRedirects(self.ingresar(), reverse('panel'))

    def test_el_correo_no_distingue_mayusculas(self):
        self.assertRedirects(self.ingresar(email='  BETO@correo.com '), reverse('panel'))

    def test_mismo_mensaje_si_el_correo_no_existe_o_la_clave_falla(self):
        a = self.ingresar(password='mala')
        b = self.ingresar(email='nadie@correo.com')
        self.assertContains(a, 'Correo o contraseña incorrectos.')
        self.assertContains(b, 'Correo o contraseña incorrectos.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_cuenta_desactivada_no_ingresa(self):
        self.usuario.is_active = False
        self.usuario.save()
        self.assertContains(self.ingresar(), 'Correo o contraseña incorrectos.')

    def test_bloqueo_tras_cinco_intentos_fallidos(self):
        for _ in range(5):
            self.ingresar(password='mala')
        # Aunque ahora la clave sea la correcta, sigue bloqueado
        r = self.ingresar()
        self.assertContains(r, 'Demasiados intentos')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_un_ingreso_correcto_reinicia_el_conteo(self):
        for _ in range(4):
            self.ingresar(password='mala')
        self.ingresar()
        self.client.post(reverse('salir'))
        for _ in range(4):
            self.ingresar(password='mala')
        self.assertRedirects(self.ingresar(), reverse('panel'))

    def test_next_dentro_del_sitio_se_respeta(self):
        r = self.ingresar(next='/admin/')
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)

    def test_next_hacia_otro_sitio_se_ignora(self):
        r = self.ingresar(next='https://sitio-malo.com/robar')
        self.assertRedirects(r, reverse('panel'))

    def test_el_panel_exige_ingresar(self):
        r = self.client.get(reverse('panel'))
        self.assertRedirects(r, reverse('ingresar') + '?next=/panel/', fetch_redirect_response=False)

    def test_la_pagina_de_ingreso_abre_la_ventana(self):
        r = self.client.get(reverse('ingresar'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['modal_abierto'], 'modal-ingresar')

    def test_formularios_exigen_csrf(self):
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        r = c.post(reverse('ingresar'), {'email': 'beto@correo.com', 'password': 'Taller-2026-ok'})
        self.assertEqual(r.status_code, 403)

    def test_panel_saluda_segun_el_rol(self):
        self.client.force_login(self.usuario)
        self.assertContains(self.client.get(reverse('panel')), 'Hola, Beto Ríos')
        tec = Usuario.objects.create_user('t@correo.com', 'Tito Técnico', 'Taller-2026-ok', rol='TECNICO')
        self.client.force_login(tec)
        self.assertContains(self.client.get(reverse('panel')), 'Panel técnico · Tito Técnico')
