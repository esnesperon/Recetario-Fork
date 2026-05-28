from datetime import datetime


class Notification:
    """Aviso dirigido a un usuario cuando alguien interactúa con su receta.

    Tipos soportados:
    - "fork": otro usuario forkeó una receta tuya.
    - "comment": otro usuario comentó en una receta tuya.
    """

    def __init__(
        self,
        recipient_username: str,
        actor_username: str,
        kind: str,
        recipe_oid: str,
    ):
        """Crea una notificación sin leer.

        :param recipient_username: usuario que la recibe.
        :param actor_username: usuario que desencadena el aviso.
        :param kind: tipo de evento ('fork' | 'comment').
        :param recipe_oid: OID seguro de la receta implicada.
        """
        self._recipient = recipient_username
        self._actor = actor_username
        self._kind = kind
        self._recipe_oid = recipe_oid
        self._read = False
        self._created_at = datetime.utcnow().isoformat()

    @property
    def recipient(self) -> str: return self._recipient

    @property
    def actor(self) -> str: return self._actor

    @property
    def kind(self) -> str: return self._kind

    @property
    def recipe_oid(self) -> str: return self._recipe_oid

    @property
    def read(self) -> bool: return self._read
    @read.setter
    def read(self, v: bool) -> None: self._read = bool(v)

    @property
    def created_at(self) -> str: return self._created_at
