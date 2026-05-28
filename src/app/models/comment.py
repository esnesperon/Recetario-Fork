from datetime import datetime


class Comment:
    """Comentario que un usuario deja sobre una receta."""

    def __init__(self, recipe_oid: str, author_username: str, text: str):
        """Crea un comentario.

        :param recipe_oid: OID seguro de la receta comentada.
        :param author_username: username del autor del comentario.
        :param text: cuerpo del comentario.
        """
        self._recipe_oid = recipe_oid
        self._author_username = author_username
        self._text = text
        self._created_at = datetime.utcnow().isoformat()

    @property
    def recipe_oid(self) -> str: return self._recipe_oid

    @property
    def author_username(self) -> str: return self._author_username
    @author_username.setter
    def author_username(self, v: str) -> None: self._author_username = v

    @property
    def text(self) -> str: return self._text

    @property
    def created_at(self) -> str: return self._created_at
