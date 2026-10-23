

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("", include("usuarios.urls")),
    path("", include("ordenes.urls")),
]

# Para ver las fotos subidas mientras se trabaja en el computador
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
