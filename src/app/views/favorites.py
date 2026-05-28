from flask import Blueprint, render_template
from flask_login import login_required, current_user

from ..extensions import srp, safe_oid, load_safe
from ..models import Favorite, Recipe, Rating

bp = Blueprint("favorites", __name__, url_prefix="/favorites")


def avg_rating(recipe_oid: str) -> tuple[float, int]:
    stars = [r.stars for r in srp.load_all(Rating) if r.recipe_oid == recipe_oid]
    return (sum(stars) / len(stars), len(stars)) if stars else (0.0, 0)


@bp.route("/")
@login_required
def mine():
    """Listado de las recetas marcadas como favoritas por el usuario."""
    items = []
    for f in srp.load_all(Favorite):
        if f.username != current_user.username:
            continue
        r = load_safe(f.recipe_oid)
        if isinstance(r, Recipe):
            avg, n = avg_rating(f.recipe_oid)
            items.append({"oid": f.recipe_oid, "r": r, "avg": avg, "n_votes": n})
    return render_template("favorites/list.html", items=items)
