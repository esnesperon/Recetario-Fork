from datetime import datetime
from typing import Optional


class Recipe:
    """Receta de cocina, con soporte para versiones tipo *fork*.

    Cada receta puede derivar de otra (`parent_oid`); la receta raíz del árbol
    se referencia en `root_oid`. Ambos campos almacenan la forma segura del
    OID de Sirope (cadena URL-safe) para ser pasados por las rutas.
    """

    def __init__(
        self,
        title: str,
        description: str,
        ingredients: list[str],
        steps: list[str],
        author_username: str,
        tag_names: Optional[list[str]] = None,
        parent_oid: Optional[str] = None,
        root_oid: Optional[str] = None,
        image_url: str = "",
    ):
        """Crea una receta.

        :param title: título visible.
        :param description: descripción breve.
        :param ingredients: lista de ingredientes (uno por elemento).
        :param steps: lista ordenada de pasos.
        :param author_username: username del autor.
        :param tag_names: etiquetas (minúsculas); pueden ser None.
        :param parent_oid: OID seguro de la receta de la que se forkea;
            None si es receta original.
        :param root_oid: OID seguro de la raíz del árbol de forks.
        """
        self._title = title
        self._description = description
        self._ingredients = list(ingredients)
        self._steps = list(steps)
        self._author_username = author_username
        self._tag_names = list(tag_names or [])
        self._parent_oid = parent_oid
        self._root_oid = root_oid
        self._image_url = image_url
        self._created_at = datetime.utcnow().isoformat()

    @property
    def title(self) -> str: return self._title
    @title.setter
    def title(self, v: str) -> None: self._title = v

    @property
    def description(self) -> str: return self._description
    @description.setter
    def description(self, v: str) -> None: self._description = v

    @property
    def ingredients(self) -> list[str]: return list(self._ingredients)
    @ingredients.setter
    def ingredients(self, v: list[str]) -> None: self._ingredients = list(v)

    @property
    def steps(self) -> list[str]: return list(self._steps)
    @steps.setter
    def steps(self, v: list[str]) -> None: self._steps = list(v)

    @property
    def author_username(self) -> str: return self._author_username
    @author_username.setter
    def author_username(self, v: str) -> None: self._author_username = v

    @property
    def tag_names(self) -> list[str]: return list(self._tag_names)
    @tag_names.setter
    def tag_names(self, v: list[str]) -> None: self._tag_names = list(v)

    @property
    def parent_oid(self) -> Optional[str]: return self._parent_oid
    @parent_oid.setter
    def parent_oid(self, v: Optional[str]) -> None: self._parent_oid = v

    @property
    def root_oid(self) -> Optional[str]: return self._root_oid
    @root_oid.setter
    def root_oid(self, v: Optional[str]) -> None: self._root_oid = v

    @property
    def image_url(self) -> str: return getattr(self, "_image_url", "") or ""
    @image_url.setter
    def image_url(self, v: str) -> None: self._image_url = v

    @property
    def created_at(self) -> str: return self._created_at

    def is_fork(self) -> bool:
        """True si esta receta es un fork de otra."""
        return self._parent_oid is not None

    def diff_against(self, other: "Recipe") -> dict:
        """Calcula las diferencias frente a otra receta (típicamente el padre).

        :param other: receta contra la que comparar.
        :return: dict con:
            - ingredients_added: ingredientes presentes aquí y no en other.
            - ingredients_removed: ingredientes presentes en other y no aquí.
            - steps_changed: bool, True si la lista de pasos difiere.
            - my_steps / parent_steps: ambas listas de pasos.
        """
        my_ing = set(self._ingredients)
        ot_ing = set(other._ingredients)
        return {
            "ingredients_added": sorted(my_ing - ot_ing),
            "ingredients_removed": sorted(ot_ing - my_ing),
            "steps_changed": self._steps != other._steps,
            "my_steps": list(self._steps),
            "parent_steps": list(other._steps),
        }
