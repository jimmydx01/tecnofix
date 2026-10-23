from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def dinero(valor):
    """Muestra un número como dinero: 40 -> $40.00"""
    try:
        return f'${Decimal(valor):,.2f}'
    except (InvalidOperation, TypeError, ValueError):
        return valor


@register.filter
def numero_limpio(valor):
    """Número para un <input>: siempre con punto decimal y sin ceros sobrantes (40.00 -> 40, 12.50 -> 12.5)."""
    try:
        texto = f'{Decimal(valor):f}'
    except (InvalidOperation, TypeError, ValueError):
        return valor
    return texto.rstrip('0').rstrip('.') if '.' in texto else texto
