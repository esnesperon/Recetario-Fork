class Favorite:
    """Marca de "favorito" de un usuario sobre una receta.

    La unicidad (un único favorito por usuario y receta) se aplica en las
    vistas: al pulsar el botón, si ya existe se elimina (toggle).
    """

    def __init__(self, username: str, recipe_oid: str):
        """Crea un favorito.

        :param username: usuario que marca.
        :param recipe_oid: OID seguro de la receta marcada.
        """
        self._username = username
        self._recipe_oid = recipe_oid

    @property
    def username(self) -> str: return self._username

    @property
    def recipe_oid(self) -> str: return self._recipe_oid
