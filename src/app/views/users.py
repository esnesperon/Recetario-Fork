from flask import Blueprint, render_template, abort

from ..extensions import srp, safe_oid
from ..models import User, Recipe, Rating

bp = Blueprint("users", __name__, url_prefix="/user")


def _find_user(username: str):
    """Devuelve el User con ese username, o None si no existe."""
    return next(
        (u for u in srp.load_all(User) if u.username == username),
        None,
    )


@bp.route("/<username>")
def profile(username):
    """Perfil público del usuario: listado de sus recetas y estadísticas."""
    user = _find_user(username)
    if user is None:
        abort(404)

    user_recipes = [(safe_oid(r), r) for r in srp.load_all(Recipe)
                    if r.author_username == username]

    n_originals = sum(1 for _, r in user_recipes if r.parent_oid is None)
    n_forks = len(user_recipes) - n_originals

    oids = {oid for oid, _ in user_recipes}
    rs = [r for r in srp.load_all(Rating) if r.recipe_oid in oids]
    avg_received = (sum(r.stars for r in rs) / len(rs)) if rs else 0.0

    recipe_items = []
    for oid, r in user_recipes:
        star_list = [rt.stars for rt in rs if rt.recipe_oid == oid]
        avg = (sum(star_list) / len(star_list)) if star_list else 0.0
        n = len(star_list)
        recipe_items.append({"oid": oid, "r": r, "avg": avg, "n_votes": n})
    recipe_items.sort(key=lambda x: x["r"].created_at, reverse=True)

    return render_template(
        "users/profile.html",
        username=username,
        email=user.email,
        items=recipe_items,
        n_originals=n_originals,
        n_forks=n_forks,
        n_total=len(user_recipes),
        n_ratings=len(rs),
        avg_received=avg_received,
    )
