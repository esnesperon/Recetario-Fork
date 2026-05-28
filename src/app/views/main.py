from flask import Blueprint, render_template, request

from ..extensions import srp, safe_oid
from ..models import Recipe, Rating

bp = Blueprint("main", __name__)


def avg_rating(recipe_oid: str) -> tuple[float, int]:
    """Calcula la media de estrellas y el número de votos de una receta.

    :param recipe_oid: OID seguro de la receta.
    :return: (media, n_votos); (0.0, 0) si aún no hay valoraciones.
    """
    stars = [r.stars for r in srp.load_all(Rating) if r.recipe_oid == recipe_oid]
    return (sum(stars) / len(stars), len(stars)) if stars else (0.0, 0)


@bp.route("/")
def index():
    """Listado principal de recetas con filtros opcionales.

    Acepta los siguientes parámetros GET:
    - q: búsqueda por texto en título o descripción.
    - tag: filtra por una etiqueta concreta.
    - author: filtra por username del autor.
    """
    q = (request.args.get("q") or "").strip().lower()
    tag = (request.args.get("tag") or "").strip().lower()
    author = (request.args.get("author") or "").strip()
    recipes = list(srp.load_all(Recipe))

    if q:
        recipes = [
            r for r in recipes
            if q in r.title.lower() or q in r.description.lower()
        ]
    if tag:
        recipes = [r for r in recipes if tag in [t.lower() for t in r.tag_names]]
    if author:
        recipes = [r for r in recipes if r.author_username == author]

    items = []
    for r in recipes:
        oid = safe_oid(r)
        avg, n = avg_rating(oid)
        items.append({"oid": oid, "r": r, "avg": avg, "n_votes": n})
    items.sort(key=lambda x: x["r"].created_at, reverse=True)

    return render_template("index.html", items=items, q=q, tag=tag, author=author)
