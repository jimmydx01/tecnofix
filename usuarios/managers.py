from django.contrib.auth.base_user import BaseUserManager


class UsuarioManager(BaseUserManager):
    """Crea usuarios que ingresan con su correo y no con un nombre de usuario."""

    use_in_migrations = True

    def _crear(self, email, nombre, password, **extra):
        if not email:
            raise ValueError('El correo es obligatorio.')
        usuario = self.model(email=self.normalize_email(email), nombre=nombre, **extra)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, nombre, password=None, **extra):
        extra.setdefault('is_staff', False)
        extra.setdefault('is_superuser', False)
        return self._crear(email, nombre, password, **extra)

    def create_superuser(self, email, nombre, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('rol', 'ADMIN')
        if not extra['is_staff'] or not extra['is_superuser']:
            raise ValueError('Un superusuario debe tener is_staff e is_superuser en True.')
        return self._crear(email, nombre, password, **extra)
