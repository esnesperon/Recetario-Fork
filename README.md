# Recetario con versiones tipo fork (ALS)

Aplicación web Flask + Jinja2 + Sirope/Redis + Flask-Login donde los usuarios publican recetas y pueden **forkear** las de otros para crear variantes. Cada receta tiene un árbol de versiones (similar al de GitHub) y se puede ver el diff (las diferencias de ingredientes y pasos) frente a su padre.

## Entidades (6, sin contar usuarios)
La aplicación fue diseñada para la **máxima complejidad y calificación**, manejando **6 entidades distintas** almacenadas en Redis mediante Sirope:
- **Recipe**: receta con título, descripción, ingredientes, pasos, etiquetas e imagen. Posee `parent_oid` y `root_oid` para construir el árbol de forks.
- **Comment**: comentarios en texto que dejan los usuarios en una receta.
- **Rating**: valoración de 1-5 estrellas (una única por usuario y receta).
- **Favorite**: guarda las recetas favoritas de cada usuario de forma individual.
- **Notification**: notificaciones del sistema (por ejemplo, cuando alguien hace un fork o comenta en tu receta).
- **Tag**: etiquetas descriptivas asociadas a las recetas para facilitar la búsqueda y el filtrado.

## Requisitos
- Python 3.11+
- Redis corriendo en local (por defecto `localhost:6379`)

## Instalación rápida (Windows)
```powershell
cd src
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

*(En Linux/Mac: `source .venv/bin/activate`)*

## Ejecución
Asegúrate de que Redis está ejecutándose en tu máquina. En una terminal nueva:
```bash
redis-server &
```

Vuelve a la terminal de tu entorno virtual en la carpeta `src`. Tienes varias alternativas para iniciar la aplicación:

**Opción 1: Usando el script principal (Desarrollo)**
```bash
python run.py
```

**Opción 2: Usando la CLI de Flask (Desarrollo)**
```bash
flask --app run run --debug
```

**Opción 3: Usando Waitress (Producción en Windows)**
```bash
pip install waitress
waitress-serve --port=5000 run:app
```
La aplicación estará disponible en 👉 <http://127.0.0.1:5000>.

## Características de Seguridad y Robustez (Recientes)
- **Hashing de Contraseñas Fuerte**: Integración con `werkzeug.security` para usar algoritmos modernos (scrypt/pbkdf2) con *salting* automático, abandonando los hashes directos débiles (SHA-256).
- **Protección Global CSRF**: Integración de `Flask-WTF CSRFProtect` en toda la aplicación, protegiendo tanto los formularios HTML tradicionales como todas las llamadas asíncronas de **HTMX** inyectadas globalmente desde `base.html`.
- **Integridad Estructural de Forks**: Lógica recursiva que protege el árbol de versiones. Al borrar un nodo intermedio, los forks hijos y toda su descendencia se independizan correctamente creando nuevos sub-árboles consistentes.
- **Carga de Archivos Segura**: Gestión unificada de subidas de imágenes mediante directorios estáticos protegidos de Flask (`/static/uploads/`).

## Estructura del Código
```
/
  README.md
  doc/                  # Documentación del proyecto
    diagramas/          # Diagramas (arquitectura, BD, etc.)
    documentacion_practica.pdf # Memoria del proyecto en PDF
    info.txt            # Información del alumno y enlaces
  src/
    run.py              # Script de entrada
    config.py           # Configuración y variables de entorno
    requirements.txt    # Dependencias
    app/
      __init__.py       # Application Factory
      extensions.py     # Inicialización de Sirope, LoginManager y CSRFProtect
      errors.py         # Manejadores de error globales (404, 500...)
      forms.py          # Definición de formularios WTForms
      models/           # Modelos de datos (User, Recipe, Comment, etc.)
      views/            # Controladores estructurados por Blueprints
      templates/        # Vistas (Jinja2) potenciadas con HTMX
      static/           # CSS y almacenamiento de subidas (uploads)
```

## Notas de diseño e Interacción
- Los OIDs de Sirope viajan por la URL en formato seguro (`srp.safe_from_oid`).
- **HTMX** se utiliza estratégicamente para recargar y renderizar valoraciones, comentarios y acciones rápidas sin necesidad de recargar la página ni programar Vanilla JS (ofreciendo experiencia SPA fluida).
- La aplicación inyecta variables globales en plantillas mediante `context_processor` (por ejemplo, conteo de notificaciones sin leer en el menú).
