from flask import render_template


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, msg="Página no encontrada."), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template(
            "error.html",
            code=500,
            msg="Ha ocurrido un error inesperado. Puedes volver al inicio e intentarlo de nuevo.",
        ), 500
