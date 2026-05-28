class Tag:
    """Etiqueta (categoría libre) asociada a recetas.

    El nombre se normaliza a minúsculas y sin espacios sobrantes para evitar
    duplicados del tipo "Postre" / "postre ".
    """

    def __init__(self, name: str):
        """Crea una etiqueta.

        :param name: nombre; se almacena en minúsculas y recortado.
        """
        self._name = name.strip().lower()

    @property
    def name(self) -> str: return self._name

    def __eq__(self, other):
        return isinstance(other, Tag) and other._name == self._name

    def __hash__(self):
        return hash(self._name)
