from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin):
    """Usuario de la aplicación.

    Se integra con Flask-Login vía UserMixin. La contraseña nunca se almacena
    en claro: se guarda su hash seguro usando werkzeug.security. La identidad 
    del usuario es su username (único), que también se usa como `get_id()` 
    para las sesiones.
    """

    def __init__(self, username: str, password: str, email: str = ""):
        """Crea un usuario.

        :param username: nombre único (se usa como ID en Flask-Login).
        :param password: contraseña en claro; se almacena hasheada.
        :param email: correo opcional.
        """
        self._username = username
        self._email = email
        self._pwd_hash = generate_password_hash(password)

    def check_password(self, pwd: str) -> bool:
        """Comprueba si `pwd` coincide con la contraseña almacenada."""
        return check_password_hash(self._pwd_hash, pwd)

    def set_password(self, pwd: str) -> None:
        """Reemplaza la contraseña por una nueva (almacena su hash seguro)."""
        self._pwd_hash = generate_password_hash(pwd)

    @property
    def username(self) -> str:
        return self._username

    @property
    def email(self) -> str:
        return self._email

    def get_id(self) -> str:
        return self._username

    def __eq__(self, other):
        return isinstance(other, User) and other._username == self._username

    def __hash__(self):
        return hash(self._username)
