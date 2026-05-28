from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from ..extensions import srp
from ..models import User
from ..forms import LoginForm, RegisterForm

bp = Blueprint("auth", __name__, url_prefix="/auth")


def _find_user(username: str):
    """Devuelve el User con ese username, o None si no existe."""
    return next(
        (u for u in srp.load_all(User) if u.username == username),
        None,
    )


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Página de inicio de sesión.

    Si el usuario ya está autenticado, redirige al índice. En caso de éxito,
    respeta el parámetro `?next=` para volver al destino previsto.
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = _find_user(form.username.data.strip())
        if user and user.check_password(form.password.data):
            login_user(user)
            nxt = request.args.get("next") or url_for("main.index")
            return redirect(nxt)
        flash("Usuario o contraseña incorrectos.", "error")
    return render_template("auth/login.html", form=form)


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Registro de usuarios nuevos.

    Rechaza username duplicados. Tras crear la cuenta inicia sesión
    automáticamente y redirige al índice.
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegisterForm()
    if form.validate_on_submit():
        uname = form.username.data.strip()
        if _find_user(uname):
            flash("Ese nombre de usuario ya existe.", "error")
        else:
            u = User(uname, form.password.data, (form.email.data or "").strip())
            srp.save(u)
            login_user(u)
            flash("Cuenta creada. ¡Bienvenido!", "success")
            return redirect(url_for("main.index"))
    return render_template("auth/register.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    """Cierra la sesión del usuario actual y vuelve al índice."""
    logout_user()
    return redirect(url_for("main.index"))
