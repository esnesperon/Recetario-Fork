from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Optional, NumberRange, Email, URL


class LoginForm(FlaskForm):
    username = StringField("Usuario", validators=[DataRequired(), Length(3, 40)])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    submit = SubmitField("Entrar")


class RegisterForm(FlaskForm):
    username = StringField("Usuario", validators=[DataRequired(), Length(3, 40)])
    email = StringField("Correo", validators=[Optional(), Email(), Length(max=120)])
    password = PasswordField("Contraseña", validators=[DataRequired(), Length(min=4)])
    confirm = PasswordField(
        "Confirmar contraseña",
        validators=[DataRequired(), EqualTo("password", "Las contraseñas no coinciden.")],
    )
    submit = SubmitField("Registrarse")


class RecipeForm(FlaskForm):
    title = StringField("Título", validators=[DataRequired(), Length(1, 120)])
    description = TextAreaField("Descripción", validators=[Optional(), Length(max=500)])
    ingredients = TextAreaField(
        "Ingredientes (uno por línea)",
        validators=[DataRequired()],
        render_kw={"rows": 6, "placeholder": "200 g harina\n2 huevos\n..."},
    )
    steps = TextAreaField(
        "Pasos (uno por línea)",
        validators=[DataRequired()],
        render_kw={"rows": 8, "placeholder": "Mezclar los ingredientes\nHornear 20 min\n..."},
    )
    tags = StringField(
        "Etiquetas (separadas por coma)",
        validators=[Optional(), Length(max=200)],
        render_kw={"placeholder": "postre, rápido, vegano"},
    )
    image_url = StringField(
        "URL de la imagen (opcional)",
        validators=[Optional(), URL(message="Debe ser una URL válida."), Length(max=500)],
        render_kw={"placeholder": "https://…/foto.jpg"},
    )
    image_file = FileField(
        "O sube una imagen",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "gif", "webp"], "Solo imágenes (jpg, png, gif, webp).")],
    )
    submit = SubmitField("Guardar")


class CommentForm(FlaskForm):
    text = TextAreaField("Comentario", validators=[DataRequired(), Length(1, 500)])
    submit = SubmitField("Comentar")


class RatingForm(FlaskForm):
    stars = IntegerField("Estrellas (1-5)", validators=[DataRequired(), NumberRange(1, 5)])
    submit = SubmitField("Valorar")
