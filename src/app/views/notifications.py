from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from ..extensions import srp, safe_oid, load_safe
from ..models import Notification, Recipe

bp = Blueprint("notifications", __name__, url_prefix="/notifications")


def unread_count_for(username: str) -> int:
    """Número de notificaciones sin leer del usuario."""
    return sum(
        1 for n in srp.load_all(Notification)
        if n.recipient == username and not n.read
    )


@bp.route("/")
@login_required
def inbox():
    """Bandeja de notificaciones; al visitarla se marcan todas como leídas."""
    items = []
    for n in srp.load_all(Notification):
        if n.recipient != current_user.username:
            continue
        r = load_safe(n.recipe_oid)
        title = r.title if isinstance(r, Recipe) else "(receta eliminada)"
        exists = isinstance(r, Recipe)
        items.append({
            "oid": safe_oid(n),
            "n": n,
            "recipe_title": title,
            "recipe_exists": exists,
        })
    items.sort(key=lambda p: p["n"].created_at, reverse=True)

    # Marcar como leídas al entrar.
    for n in srp.load_all(Notification):
        if n.recipient == current_user.username and not n.read:
            n.read = True
            srp.save(n)

    return render_template("notifications/inbox.html", items=items)


@bp.route("/clear", methods=["POST"])
@login_required
def clear():
    """Elimina todas las notificaciones del usuario."""
    for n in srp.load_all(Notification):
        if n.recipient == current_user.username:
            srp.delete(n.__oid__)
    return redirect(url_for("notifications.inbox"))
