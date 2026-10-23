"""Protección contra adivinar contraseñas: se limita el número de intentos fallidos."""

import hashlib

from django.core.cache import cache

MAX_INTENTOS_CUENTA = 5    # fallos permitidos por correo desde un mismo equipo
MAX_INTENTOS_EQUIPO = 30   # fallos permitidos desde un mismo equipo, con cualquier correo
VENTANA = 15 * 60          # el bloqueo dura 15 minutos
MENSAJE_BLOQUEO = 'Demasiados intentos fallidos. Espera 15 minutos e inténtalo de nuevo.'


def _claves(request, email):
    ip = request.META.get('REMOTE_ADDR', 'desconocida')
    huella = hashlib.sha256(email.encode()).hexdigest()[:24]
    return f'ingreso:cuenta:{ip}:{huella}', f'ingreso:equipo:{ip}'


def bloqueado(request, email):
    cuenta, equipo = _claves(request, email)
    return cache.get(cuenta, 0) >= MAX_INTENTOS_CUENTA or cache.get(equipo, 0) >= MAX_INTENTOS_EQUIPO


def _sumar(clave):
    # add() solo crea la clave si no existe, así la ventana empieza en el primer fallo
    if not cache.add(clave, 1, VENTANA):
        try:
            cache.incr(clave)
        except ValueError:
            cache.set(clave, 1, VENTANA)


def registrar_fallo(request, email):
    for clave in _claves(request, email):
        _sumar(clave)


def limpiar(request, email):
    cache.delete(_claves(request, email)[0])
