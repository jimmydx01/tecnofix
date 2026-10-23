from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse

from ordenes.models import Orden, Servicio
from .models import Usuario

CLAVE = 'Taller-2026-ok'


def nuevo(email, nombre, rol='CLIENTE', **extra):
    return Usuario.objects.create_user(email, nombre, CLAVE, rol=rol, **extra)


class Base(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser('admin@correo.com', 'Admin Uno', CLAVE)
        self.servicio = Servicio.objects.create(nombre='Laptops', precio_base=40)

    def ingresar_admin(self):
        self.client.force_login(self.admin)

    def mensajes(self, respuesta):
        return [str(m) for m in get_messages(respuesta.wsgi_request)]

    def orden(self, cliente, tecnico=None, estado='RECIBIDO'):
        extra = {}
        if estado == 'ENTREGADO':
            from django.utils import timezone
            extra = {'entrega_autorizada': True, 'entregada_en': timezone.now()}
        return Orden.objects.create(cliente=cliente, tecnico=tecnico, servicio=self.servicio, modelo='HP', estado=estado, **extra)


class PermisosTests(Base):
    def test_las_pantallas_exigen_ingresar(self):
        for nombre in ('personal', 'clientes'):
            r = self.client.get(reverse(nombre))
            self.assertEqual(r.status_code, 302)
            self.assertIn('/ingresar/', r['Location'])

    def test_cliente_y_tecnico_no_entran(self):
        for u in (nuevo('c@correo.com', 'Cli Uno'), nuevo('t@correo.com', 'Tec Uno', 'TECNICO')):
            self.client.force_login(u)
            for nombre in ('personal', 'clientes'):
                r = self.client.get(reverse(nombre))
                self.assertRedirects(r, reverse('panel'))
            self.assertEqual(self.client.get(reverse('panel')).status_code, 200)

    def test_cliente_no_puede_usar_las_acciones(self):
        cli = nuevo('c@correo.com', 'Cli Uno')
        otro = nuevo('o@correo.com', 'Otro Cli')
        self.client.force_login(cli)
        self.client.post(reverse('usuario_eliminar', args=[otro.pk]))
        self.client.post(reverse('usuario_estado', args=[otro.pk]))
        otro.refresh_from_db()
        self.assertTrue(otro.is_active)

    def test_las_acciones_solo_aceptan_post(self):
        self.ingresar_admin()
        cli = nuevo('c@correo.com', 'Cli Uno')
        self.assertEqual(self.client.get(reverse('usuario_eliminar', args=[cli.pk])).status_code, 405)
        self.assertEqual(self.client.get(reverse('usuario_estado', args=[cli.pk])).status_code, 405)

    def test_las_acciones_exigen_csrf(self):
        cli = nuevo('c@correo.com', 'Cli Uno')
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.admin)
        self.assertEqual(c.post(reverse('usuario_eliminar', args=[cli.pk])).status_code, 403)

    def test_el_administrador_ve_su_panel_con_pestanas(self):
        self.ingresar_admin()
        r = self.client.get(reverse('panel'))
        self.assertContains(r, 'Panel de administración')
        self.assertContains(r, 'Personal')
        self.assertContains(r, 'Clientes')


class PersonalTests(Base):
    def setUp(self):
        super().setUp()
        self.ingresar_admin()

    def alta(self, **cambios):
        datos = {'nombre': 'Carlos Técnico', 'email': 'carlos@taller.com', 'password': CLAVE, **cambios}
        return self.client.post(reverse('personal'), datos)

    def test_alta_de_tecnico(self):
        r = self.alta()
        self.assertRedirects(r, reverse('personal'))
        t = Usuario.objects.get(email='carlos@taller.com')
        self.assertEqual(t.rol, Usuario.Rol.TECNICO)
        self.assertFalse(t.is_staff)
        self.assertTrue(t.check_password(CLAVE))

    def test_el_tecnico_nuevo_puede_ingresar(self):
        self.alta()
        self.client.logout()
        r = self.client.post(reverse('ingresar'), {'email': 'carlos@taller.com', 'password': CLAVE})
        self.assertRedirects(r, reverse('cambiar_contrasena'), fetch_redirect_response=False)

    def test_el_alta_no_permite_elegir_rol(self):
        self.alta(rol='ADMIN', is_staff='on')
        self.assertEqual(Usuario.objects.get(email='carlos@taller.com').rol, 'TECNICO')

    def test_validaciones_del_alta(self):
        self.assertContains(self.alta(email='malo'), 'correo válido')
        self.assertContains(self.alta(password='12345678'), 'demasiado')
        self.assertContains(self.alta(nombre='Carlos99'), 'letras')
        self.alta()
        self.assertContains(self.alta(email='CARLOS@taller.com'), 'ya está registrado')
        self.assertEqual(Usuario.objects.filter(rol='TECNICO').count(), 1)

    def test_lista_solo_tecnicos_y_busca(self):
        nuevo('a@t.com', 'Ana Técnica', 'TECNICO')
        nuevo('b@t.com', 'Beto Técnico', 'TECNICO')
        nuevo('c@c.com', 'Carla Cliente')
        r = self.client.get(reverse('personal'))
        self.assertContains(r, 'Ana Técnica')
        self.assertNotContains(r, 'Carla Cliente')
        r = self.client.get(reverse('personal'), {'q': 'beto'})
        self.assertContains(r, 'Beto Técnico')
        self.assertNotContains(r, 'Ana Técnica')
        self.assertContains(self.client.get(reverse('personal'), {'q': 'zzz'}), 'No hay personal')

    def test_cuenta_los_servicios_activos_de_cada_tecnico(self):
        t = nuevo('a@t.com', 'Ana Técnica', 'TECNICO')
        c = nuevo('c@c.com', 'Carla Cliente')
        self.orden(c, t, 'REPARACION')
        self.orden(c, t, 'ENTREGADO')
        self.assertContains(self.client.get(reverse('personal')), '1 activo')

    def test_paginacion(self):
        for i in range(12):
            nuevo(f't{i}@t.com', f'Tecnico {chr(65 + i)}', 'TECNICO')
        r = self.client.get(reverse('personal'))
        self.assertEqual(len(r.context['pagina']), 10)
        self.assertContains(r, 'Página 1 de 2')
        self.assertEqual(len(self.client.get(reverse('personal'), {'pagina': 2}).context['pagina']), 2)

    def test_desactivar_impide_ingresar_y_activar_lo_devuelve(self):
        t = nuevo('a@t.com', 'Ana Técnica', 'TECNICO')
        self.client.post(reverse('usuario_estado', args=[t.pk]))
        t.refresh_from_db()
        self.assertFalse(t.is_active)
        otro = Client()
        r = otro.post(reverse('ingresar'), {'email': 'a@t.com', 'password': CLAVE})
        self.assertContains(r, 'Correo o contraseña incorrectos.')
        self.client.post(reverse('usuario_estado', args=[t.pk]))
        t.refresh_from_db()
        self.assertTrue(t.is_active)

    def test_desactivar_cierra_la_sesion_abierta(self):
        t = nuevo('a@t.com', 'Ana Técnica', 'TECNICO')
        otro = Client()
        otro.force_login(t)
        self.assertEqual(otro.get(reverse('panel')).status_code, 200)
        self.client.post(reverse('usuario_estado', args=[t.pk]))
        self.assertEqual(otro.get(reverse('panel')).status_code, 302)

    def test_eliminar_tecnico_sin_servicios_activos(self):
        t = nuevo('a@t.com', 'Ana Técnica', 'TECNICO')
        r = self.client.post(reverse('usuario_eliminar', args=[t.pk]))
        self.assertRedirects(r, reverse('personal'))
        self.assertFalse(Usuario.objects.filter(pk=t.pk).exists())

    def test_no_se_elimina_un_tecnico_con_servicios_activos(self):
        t = nuevo('a@t.com', 'Ana Técnica', 'TECNICO')
        self.orden(nuevo('c@c.com', 'Carla Cliente'), t, 'REPARACION')
        r = self.client.post(reverse('usuario_eliminar', args=[t.pk]))
        self.assertTrue(Usuario.objects.filter(pk=t.pk).exists())
        self.assertIn('servicio(s) activo(s)', self.mensajes(r)[0])

    def test_tecnico_con_servicios_entregados_se_elimina_y_el_servicio_queda(self):
        t = nuevo('a@t.com', 'Ana Técnica', 'TECNICO')
        o = self.orden(nuevo('c@c.com', 'Carla Cliente'), t, 'ENTREGADO')
        self.client.post(reverse('usuario_eliminar', args=[t.pk]))
        self.assertFalse(Usuario.objects.filter(pk=t.pk).exists())
        o.refresh_from_db()
        self.assertIsNone(o.tecnico)

    def test_no_se_puede_gestionar_a_un_administrador(self):
        otro = Usuario.objects.create_superuser('otro@correo.com', 'Admin Dos', CLAVE)
        self.assertEqual(self.client.post(reverse('usuario_eliminar', args=[otro.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('usuario_estado', args=[self.admin.pk])).status_code, 404)
        self.assertTrue(Usuario.objects.filter(pk=otro.pk).exists())

    def test_volver_solo_a_direcciones_del_sitio(self):
        t = nuevo('a@t.com', 'Ana Técnica', 'TECNICO')
        r = self.client.post(reverse('usuario_estado', args=[t.pk]), {'volver': 'https://sitio-malo.com'})
        self.assertRedirects(r, reverse('personal'))
        r = self.client.post(reverse('usuario_estado', args=[t.pk]), {'volver': '/panel/personal/?q=ana'})
        self.assertRedirects(r, '/panel/personal/?q=ana')


class ClientesTests(Base):
    def setUp(self):
        super().setUp()
        self.ingresar_admin()

    def test_lista_solo_clientes_con_conteo_de_servicios(self):
        c = nuevo('c@c.com', 'Carla Cliente', telefono='0991234567')
        nuevo('t@t.com', 'Tito Técnico', 'TECNICO')
        self.orden(c)
        self.orden(c)
        r = self.client.get(reverse('clientes'))
        self.assertContains(r, 'Carla Cliente')
        self.assertContains(r, '2 servicios')
        self.assertNotContains(r, 'Tito Técnico')

    def test_busca_por_nombre_correo_o_telefono(self):
        nuevo('c@c.com', 'Carla Cliente', telefono='0991234567')
        nuevo('d@d.com', 'Diego Cliente', telefono='0987654321')
        for texto in ('carla', 'c@c', '0991'):
            r = self.client.get(reverse('clientes'), {'q': texto})
            self.assertContains(r, 'Carla Cliente')
            self.assertNotContains(r, 'Diego Cliente')

    def test_no_se_elimina_un_cliente_con_servicios(self):
        c = nuevo('c@c.com', 'Carla Cliente')
        self.orden(c)
        r = self.client.post(reverse('usuario_eliminar', args=[c.pk]))
        self.assertTrue(Usuario.objects.filter(pk=c.pk).exists())
        self.assertIn('tiene historial', self.mensajes(r)[0])
        self.assertRedirects(r, reverse('clientes'))

    def test_cliente_sin_servicios_se_elimina(self):
        c = nuevo('c@c.com', 'Carla Cliente')
        self.client.post(reverse('usuario_eliminar', args=[c.pk]))
        self.assertFalse(Usuario.objects.filter(pk=c.pk).exists())

    def test_cliente_desactivado_aparece_marcado(self):
        c = nuevo('c@c.com', 'Carla Cliente')
        self.client.post(reverse('usuario_estado', args=[c.pk]))
        self.assertContains(self.client.get(reverse('clientes')), 'Desactivado')
