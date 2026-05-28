import os
import redis
import sirope
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

_redis_client = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    password=os.environ.get("REDIS_PASSWORD") or None,
    db=int(os.environ.get("REDIS_DB", 1)),
    decode_responses=False,
)
srp = sirope.Sirope(_redis_client)
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = "auth.login"
login_manager.login_message = "Inicia sesión para continuar."


def safe_oid(obj) -> str:
    """Devuelve la forma URL-safe del OID de un objeto gestionado por Sirope.

    :param obj: objeto previamente guardado con `srp.save(obj)`.
    :return: cadena segura para pasar por URL.
    """
    return srp.safe_from_oid(obj.__oid__)


def load_safe(safe: str):
    """Carga un objeto a partir de su OID seguro, o None si no existe.

    :param safe: cadena URL-safe tal como la devuelve `safe_oid`.
    :return: el objeto cargado, o None si la cadena no es válida o el
        objeto ya no existe en Redis.
    """
    try:
        oid = srp.oid_from_safe(safe)
    except Exception:
        return None
    if not srp.exists(oid):
        return None
    return srp.load(oid)


@login_manager.user_loader
def load_user(username: str):
    from .models import User
    return next(
        (u for u in srp.load_all(User) if u.username == username),
        None,
    )
