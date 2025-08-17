Validaciones de tipo y estilo

Requisitos
- Tener el virtualenv del proyecto activado (.venv fue detectado automáticamente).
- Herramientas: mypy, ruff y flake8 (si no están instaladas, ver comando abajo).

Instalación (desde la raíz del proyecto):

.venv/bin/pip install --upgrade pip setuptools wheel
.venv/bin/pip install mypy ruff flake8 pandas-stubs scikit-learn

Comprobaciones rápidas

# Ejecuta ruff (aplica fixes automáticos con --fix)
.venv/bin/ruff check . --fix

# Ejecuta flake8
.venv/bin/flake8 .

# Ejecuta mypy usando la configuración en pyproject.toml
.venv/bin/mypy

Ejecutar tests

# Instala pytest en el virtualenv
.venv/bin/pip install pytest

# Ejecuta los tests
.venv/bin/pytest

Notas
- `pyproject.toml` contiene configuración básica para mypy, ruff y flake8.
- Recomiendo instalar `pandas-stubs` y otros stubs para librerías externas para reducir falsos positivos en mypy.
- Si prefieres no instalar stubs, mypy está configurado con `ignore_missing_imports = true`.

Si quieres, puedo aplicar cambios automáticos sugeridos por ruff y corregir las anotaciones de tipo en `lag_transformer.py`.
