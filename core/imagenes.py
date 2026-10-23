"""Fotos de Unsplash (licencia libre) con vínculo. Se pueden cambiar desde Tarifas o el admin de Django."""


def unsplash(foto):
    return f'https://images.unsplash.com/{foto}?auto=format&fit=crop&w=900&q=70'


PORTADA = unsplash('photo-1517694712202-14dd9538aa97')

POR_SERVICIO = {
    'Reparación de computadoras': unsplash('photo-1517694712202-14dd9538aa97'),
    'Celulares y tablets': unsplash('photo-1588515603068-adb330f26e92'),
    'Impresoras': unsplash('photo-1710857679450-ecd7945dd4bd'),
    'Redes y WiFi': unsplash('photo-1745847768408-b7b83796cae6'),
    'Consolas y gaming': unsplash('photo-1654621158365-55fcf7b76fb7'),
    'Mantenimiento preventivo': unsplash('photo-1695678458092-f01ccb465ae7'),
}
