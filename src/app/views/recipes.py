import os
import uuid

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, Response, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from ..extensions import srp, safe_oid, load_safe
from ..models import Recipe, Comment, Rating, Tag, Favorite, Notification
from ..forms import RecipeForm, CommentForm, RatingForm

bp = Blueprint("recipes", __name__, url_prefix="/recipes")


# -------- helpers --------
def _split_lines(txt: str) -> list[str]:
    """Convierte un texto multilínea en una lista de líneas no vacías."""
    return [ln.strip() for ln in (txt or "").splitlines() if ln.strip()]


def _split_tags(txt: str) -> list[str]:
    """Convierte una cadena separada por comas en lista de etiquetas."""
    return [t.strip().lower() for t in (txt or "").split(",") if t.strip()]


def _ensure_tags(names: list[str]) -> None:
    """Guarda en Sirope cualquier etiqueta nueva que aún no exista.

    :param names: nombres de etiquetas (ya normalizados).
    """
    existing = {t.name for t in srp.load_all(Tag)}
    for n in names:
        if n not in existing:
            srp.save(Tag(n))
            existing.add(n)


def _ratings_for(recipe_safe: str) -> list[Rating]:
    """Lista todas las valoraciones asociadas a una receta."""
    return [r for r in srp.load_all(Rating) if r.recipe_oid == recipe_safe]


def _avg(recipe_safe: str) -> tuple[float, int]:
    """Media de estrellas y número de votos de la receta."""
    rs = _ratings_for(recipe_safe)
    return (sum(r.stars for r in rs) / len(rs), len(rs)) if rs else (0.0, 0)


def _comments_for(recipe_safe: str) -> list:
    """Comentarios de la receta, ordenados del más antiguo al más reciente.

    :return: lista de pares (oid_seguro_del_comentario, objeto Comment).
    """
    out = [(safe_oid(c), c) for c in srp.load_all(Comment) if c.recipe_oid == recipe_safe]
    out.sort(key=lambda p: p[1].created_at)
    return out


def _children_of(recipe_safe: str) -> list[tuple[str, Recipe]]:
    """Forks directos (hijos) de una receta dada."""
    return [(safe_oid(r), r) for r in srp.load_all(Recipe) if r.parent_oid == recipe_safe]


def _user_rating(recipe_safe: str, username: str) -> Rating | None:
    """Devuelve el Rating de `username` sobre la receta, o None si no votó."""
    return next(
        (r for r in _ratings_for(recipe_safe) if r.author_username == username),
        None,
    )


def _user_favorite(recipe_safe: str, username: str) -> Favorite | None:
    """Devuelve el Favorite si el usuario tiene la receta marcada, o None."""
    return next(
        (f for f in srp.load_all(Favorite)
         if f.username == username and f.recipe_oid == recipe_safe),
        None,
    )


def _notify(recipient: str, actor: str, kind: str, recipe_safe: str) -> None:
    """Crea una notificación si el receptor y el actor son distintos."""
    if recipient and actor and recipient != actor:
        srp.save(Notification(recipient, actor, kind, recipe_safe))


def _save_image(form, current_url: str = "") -> str:
    """Guarda la imagen subida (si la hay) y devuelve la ruta relativa.
    Si se sube archivo, se usa esa (prioridad).
    Si no, se usa la URL del formulario.
    Si tampoco hay URL, se conserva la imagen actual.
    """
    f = form.image_file.data
    if f and f.filename:
        ext = secure_filename(f.filename).rsplit(".", 1)[-1].lower()
        fname = f"{uuid.uuid4().hex}.{ext}"
        upload_dir = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_dir, exist_ok=True)
        f.save(os.path.join(upload_dir, fname))
        return f"/static/uploads/{fname}"
    url = (form.image_url.data or "").strip()
    return url if url else current_url


def _delete_uploaded_image(image_url: str) -> None:
    """Borra del disco un fichero subido si la URL apunta a /static/uploads/."""
    if image_url and image_url.startswith("/static/uploads/"):
        fname = image_url[len("/static/uploads/"):]
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], fname)
        if os.path.exists(path):
            os.remove(path)


# -------- CRUD --------
def _validate_recipe_form(form):
    """Si se sube un archivo de imagen, ignora errores de validación del campo URL."""
    if form.image_file.data and form.image_file.data.filename:
        form.image_url.errors = []
    return form.validate_on_submit()


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Crea una nueva receta original (sin padre)."""
    form = RecipeForm()
    if _validate_recipe_form(form):
        ing = _split_lines(form.ingredients.data)
        steps = _split_lines(form.steps.data)
        tags = _split_tags(form.tags.data)
        r = Recipe(
            title=form.title.data.strip(),
            description=(form.description.data or "").strip(),
            ingredients=ing,
            steps=steps,
            author_username=current_user.username,
            tag_names=tags,
            image_url=_save_image(form),
        )
        oid = srp.save(r)
        r.root_oid = srp.safe_from_oid(oid)
        srp.save(r)
        _ensure_tags(tags)
        flash("Receta creada.", "success")
        return redirect(url_for("recipes.detail", safe=srp.safe_from_oid(oid)))
    return render_template("recipes/form.html", form=form, mode="new", r=None)


@bp.route("/<safe>")
def detail(safe):
    """Ficha completa de una receta: ingredientes, pasos, padre, hijos,
    comentarios y valoraciones."""
    r = load_safe(safe)
    if not isinstance(r, Recipe):
        abort(404)
    comment_form = CommentForm()
    rating_form = RatingForm()
    avg, n_votes = _avg(safe)
    parent = None
    if r.parent_oid:
        parent_obj = load_safe(r.parent_oid)
        if isinstance(parent_obj, Recipe):
            parent = {"oid": r.parent_oid, "r": parent_obj}
    children = _children_of(safe)
    user_rating = None
    is_fav = False
    if current_user.is_authenticated:
        ur = _user_rating(safe, current_user.username)
        user_rating = ur.stars if ur else None
        is_fav = _user_favorite(safe, current_user.username) is not None
    return render_template(
        "recipes/detail.html",
        oid=safe,
        r=r,
        parent=parent,
        children=children,
        comments=_comments_for(safe),
        avg=avg,
        n_votes=n_votes,
        user_rating=user_rating,
        is_fav=is_fav,
        comment_form=comment_form,
        rating_form=rating_form,
    )


@bp.route("/<safe>/edit", methods=["GET", "POST"])
@login_required
def edit(safe):
    """Edita una receta existente. Solo la puede modificar su autor."""
    r = load_safe(safe)
    if not isinstance(r, Recipe):
        abort(404)
    if r.author_username != current_user.username:
        flash("Solo el autor puede editar la receta.", "error")
        return redirect(url_for("recipes.detail", safe=safe))

    form = RecipeForm()
    if request.method == "GET":
        form.title.data = r.title
        form.description.data = r.description
        form.ingredients.data = "\n".join(r.ingredients)
        form.steps.data = "\n".join(r.steps)
        form.tags.data = ", ".join(r.tag_names)
        form.image_url.data = r.image_url

    if _validate_recipe_form(form):
        clear = request.form.get("clear_image")
        if clear:
            _delete_uploaded_image(r.image_url)
            r.image_url = ""
        else:
            new_url = _save_image(form, r.image_url)
            if new_url != r.image_url:
                _delete_uploaded_image(r.image_url)
            r.image_url = new_url
        r.title = form.title.data.strip()
        r.description = (form.description.data or "").strip()
        r.ingredients = _split_lines(form.ingredients.data)
        r.steps = _split_lines(form.steps.data)
        r.tag_names = _split_tags(form.tags.data)
        srp.save(r)
        _ensure_tags(r.tag_names)
        flash("Receta actualizada.", "success")
        return redirect(url_for("recipes.detail", safe=safe))
    return render_template("recipes/form.html", form=form, mode="edit", oid=safe, r=r)


@bp.route("/<safe>/delete", methods=["POST"])
@login_required
def delete(safe):
    """Borra una receta respetando la integridad del árbol de forks.

    Política al borrar:
    - Los forks hijos se huérfanan (`parent_oid = None`) y se convierten en
      raíz de su propio subárbol (`root_oid = su propio OID`). Se preservan.
    - Los comentarios y valoraciones asociados se eliminan.
    """
    r = load_safe(safe)
    if not isinstance(r, Recipe):
        abort(404)
    if r.author_username != current_user.username:
        flash("Solo el autor puede borrar la receta.", "error")
        return redirect(url_for("recipes.detail", safe=safe))

    # Huerfanar los forks hijos y actualizar recursivamente la raíz de su subárbol.
    def _update_descendants_root(node_safe, new_root_safe):
        for c_oid, c in _children_of(node_safe):
            c.root_oid = new_root_safe
            srp.save(c)
            _update_descendants_root(c_oid, new_root_safe)

    for child_oid, child in _children_of(safe):
        child.parent_oid = None
        child.root_oid = child_oid
        srp.save(child)
        _update_descendants_root(child_oid, child_oid)

    # Borrar comentarios, valoraciones, favoritos y notificaciones asociados.
    for c in srp.load_all(Comment):
        if c.recipe_oid == safe:
            srp.delete(c.__oid__)
    for rt in srp.load_all(Rating):
        if rt.recipe_oid == safe:
            srp.delete(rt.__oid__)
    for f in srp.load_all(Favorite):
        if f.recipe_oid == safe:
            srp.delete(f.__oid__)
    for n in srp.load_all(Notification):
        if n.recipe_oid == safe:
            srp.delete(n.__oid__)

    _delete_uploaded_image(r.image_url)
    srp.delete(r.__oid__)
    flash("Receta eliminada.", "success")
    return redirect(url_for("main.index"))


# -------- fork / tree / diff --------
@bp.route("/<safe>/fork", methods=["POST"])
@login_required
def fork(safe):
    """Crea una copia editable de la receta apuntando al original como padre.

    El nuevo fork conserva ingredientes/pasos/etiquetas del padre; el usuario
    aterriza directamente en el formulario de edición para personalizarlo.
    """
    parent = load_safe(safe)
    if not isinstance(parent, Recipe):
        abort(404)
    child = Recipe(
        title=f"{parent.title} (fork de {parent.author_username})",
        description=parent.description,
        ingredients=parent.ingredients,
        steps=parent.steps,
        author_username=current_user.username,
        tag_names=parent.tag_names,
        parent_oid=safe,
        root_oid=parent.root_oid or safe,
        image_url=parent.image_url,
    )
    oid = srp.save(child)
    _notify(parent.author_username, current_user.username, "fork", safe)
    flash("Fork creado. Edítalo a tu gusto.", "success")
    return redirect(url_for("recipes.edit", safe=srp.safe_from_oid(oid)))


@bp.route("/<safe>/tree")
def tree(safe):
    """Muestra el árbol completo de versiones (forks) de una receta."""
    r = load_safe(safe)
    if not isinstance(r, Recipe):
        abort(404)
    root_safe = r.root_oid or safe
    root = load_safe(root_safe)
    if not isinstance(root, Recipe):
        root_safe = safe
        root = r

    all_recipes = [(safe_oid(x), x) for x in srp.load_all(Recipe)]

    def build(node_safe: str) -> dict:
        node = next((x for s, x in all_recipes if s == node_safe), None)
        if node is None:
            return {}
        kids = [s for s, x in all_recipes if x.parent_oid == node_safe]
        return {
            "oid": node_safe,
            "r": node,
            "is_current": node_safe == safe,
            "children": [build(k) for k in kids],
        }

    return render_template("recipes/tree.html", root=build(root_safe), current_oid=safe)


@bp.route("/<safe>/diff")
def diff(safe):
    """Muestra los cambios de la receta respecto a su receta padre."""
    r = load_safe(safe)
    if not isinstance(r, Recipe) or not r.parent_oid:
        flash("Esta receta no tiene padre con el que comparar.", "error")
        return redirect(url_for("recipes.detail", safe=safe))
    parent = load_safe(r.parent_oid)
    if not isinstance(parent, Recipe):
        flash("El padre de esta receta ya no existe.", "error")
        return redirect(url_for("recipes.detail", safe=safe))
    d = r.diff_against(parent)
    return render_template(
        "recipes/diff.html",
        oid=safe,
        r=r,
        parent_oid=r.parent_oid,
        parent=parent,
        diff=d,
    )


# -------- comments + ratings (HTMX friendly) --------
@bp.route("/<safe>/comment", methods=["POST"])
@login_required
def add_comment(safe):
    """Añade un comentario. Si la petición viene de HTMX, devuelve solo el
    fragmento HTML con la lista actualizada para inyectarla sin recargar."""
    r = load_safe(safe)
    if not isinstance(r, Recipe):
        abort(404)
    form = CommentForm()
    if form.validate_on_submit():
        c = Comment(safe, current_user.username, form.text.data.strip())
        srp.save(c)
        _notify(r.author_username, current_user.username, "comment", safe)
    if request.headers.get("HX-Request"):
        return render_template("recipes/_comments.html", comments=_comments_for(safe))
    return redirect(url_for("recipes.detail", safe=safe))


@bp.route("/<safe>/comment/<csafe>/delete", methods=["POST"])
@login_required
def delete_comment(safe, csafe):
    """Elimina un comentario propio; acepta HTMX para refresco parcial."""
    c = load_safe(csafe)
    if not isinstance(c, Comment):
        abort(404)
    if c.author_username != current_user.username:
        abort(403)
    srp.delete(c.__oid__)
    if request.headers.get("HX-Request"):
        return render_template("recipes/_comments.html", comments=_comments_for(safe))
    return redirect(url_for("recipes.detail", safe=safe))


@bp.route("/<safe>/rate", methods=["POST"])
@login_required
def rate(safe):
    """Vota (1-5 estrellas). Si el usuario ya había votado, actualiza el voto
    en lugar de crear uno nuevo (unicidad por usuario+receta)."""
    r = load_safe(safe)
    if not isinstance(r, Recipe):
        abort(404)
    form = RatingForm()
    user_stars = None
    if form.validate_on_submit():
        user_stars = form.stars.data
        existing = _user_rating(safe, current_user.username)
        if existing:
            existing.stars = user_stars
            srp.save(existing)
        else:
            srp.save(Rating(safe, current_user.username, user_stars))
    else:
        ur = _user_rating(safe, current_user.username)
        user_stars = ur.stars if ur else None
    avg, n = _avg(safe)
    if request.headers.get("HX-Request"):
        return render_template(
            "recipes/_rating.html",
            oid=safe,
            avg=avg,
            n_votes=n,
            user_rating=user_stars,
            rating_form=RatingForm(),
        )
    return redirect(url_for("recipes.detail", safe=safe))


# -------- favoritos / merge / export --------
@bp.route("/<safe>/favorite", methods=["POST"])
@login_required
def toggle_favorite(safe):
    """Marca o desmarca la receta como favorita del usuario actual."""
    r = load_safe(safe)
    if not isinstance(r, Recipe):
        abort(404)
    existing = _user_favorite(safe, current_user.username)
    if existing:
        srp.delete(existing.__oid__)
        state = False
    else:
        srp.save(Favorite(current_user.username, safe))
        state = True
    if request.headers.get("HX-Request"):
        return render_template("recipes/_fav_btn.html", oid=safe, is_fav=state)
    return redirect(url_for("recipes.detail", safe=safe))


@bp.route("/<safe>/merge-from-parent", methods=["POST"])
@login_required
def merge_from_parent(safe):
    """Trae ingredientes y pasos actuales del padre al fork (sobreescribe)."""
    r = load_safe(safe)
    if not isinstance(r, Recipe):
        abort(404)
    if r.author_username != current_user.username:
        flash("Solo el autor del fork puede traer cambios.", "error")
        return redirect(url_for("recipes.detail", safe=safe))
    if not r.parent_oid:
        flash("Esta receta no tiene padre del que traer cambios.", "error")
        return redirect(url_for("recipes.detail", safe=safe))
    parent = load_safe(r.parent_oid)
    if not isinstance(parent, Recipe):
        flash("El padre ya no existe.", "error")
        return redirect(url_for("recipes.detail", safe=safe))
    r.ingredients = parent.ingredients
    r.steps = parent.steps
    srp.save(r)
    flash("Cambios del padre aplicados.", "success")
    return redirect(url_for("recipes.detail", safe=safe))


@bp.route("/<safe>/export")
def export_md(safe):
    """Descarga la receta en formato Markdown."""
    r = load_safe(safe)
    if not isinstance(r, Recipe):
        abort(404)
    lines = [f"# {r.title}", ""]
    if r.description:
        lines += [r.description, ""]
    lines.append(f"*Autor: {r.author_username}*")
    if r.tag_names:
        lines.append("Etiquetas: " + ", ".join(f"#{t}" for t in r.tag_names))
    lines += ["", "## Ingredientes", ""]
    lines += [f"- {i}" for i in r.ingredients]
    lines += ["", "## Pasos", ""]
    lines += [f"{n}. {s}" for n, s in enumerate(r.steps, 1)]
    body = "\n".join(lines) + "\n"
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in r.title)[:60] or "receta"
    return Response(
        body,
        mimetype="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.md"'},
    )
