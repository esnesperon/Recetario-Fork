class Rating:
    """Valoración (1-5 estrellas) de un usuario sobre una receta.

    La unicidad (un único rating por usuario y receta) se garantiza en la capa
    de vistas: al votar, si ya existe un Rating del usuario para la receta se
    actualizan sus estrellas en lugar de crear uno nuevo.
    """

    def __init__(self, recipe_oid: str, author_username: str, stars: int):
        """Crea una valoración.

        :param recipe_oid: OID seguro de la receta valorada.
        :param author_username: username del votante.
        :param stars: número de estrellas (se recorta al rango [1, 5]).
        """
        self._recipe_oid = recipe_oid
        self._author_username = author_username
        self._stars = max(1, min(5, int(stars)))

    @property
    def recipe_oid(self) -> str: return self._recipe_oid

    @property
    def author_username(self) -> str: return self._author_username

    @property
    def stars(self) -> int: return self._stars
    @stars.setter
    def stars(self, v: int) -> None: self._stars = max(1, min(5, int(v)))
