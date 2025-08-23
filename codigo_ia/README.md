Validaciones de tipo y estilo

Requisitos
- Tener el virtualenv del proyecto activado (.venv fue detectado automáticamente).
- Herramientas: mypy, ruff y flake8 (si no están instaladas, ver comando abajo).

Instalación (desde la raíz del proyecto):

.venv/bin/pip install --upgrade pip setuptools wheel
.venv/bin/pip install mypy ruff flake8 pandas-stubs scikit-learn pytest pre-commit

Comprobaciones rápidas

# Ejecuta ruff (aplica fixes automáticos con --fix)
.venv/bin/ruff check . --fix

# Ejecuta flake8
.venv/bin/flake8 .

# Ejecuta mypy usando la configuración en pyproject.toml
.venv/bin/mypy

Ejecutar tests

# Ejecuta los tests (pytest ya está instalado en las dependencias)
.venv/bin/pytest

Pre-commit hooks

# Instala pre-commit
.venv/bin/pip install pre-commit

# Instala los hooks en el repositorio git
.venv/bin/pre-commit install

# Ejecuta todos los hooks manualmente (opcional)
.venv/bin/pre-commit run --all-files

# Los hooks se ejecutarán automáticamente en cada commit y validarán:
# - Ruff: linting y formateo automático en archivos de src/
# - Flake8: validaciones de estilo en archivos de src/
# - MyPy: verificación de tipos en archivos de src/
# - Pytest: ejecución de tests cuando cambien archivos de src/ o tests/

Notas
- `pyproject.toml` contiene configuración básica para mypy, ruff y flake8.
- Recomiendo instalar `pandas-stubs` y otros stubs para librerías externas para reducir falsos positivos en mypy.
- Si prefieres no instalar stubs, mypy está configurado con `ignore_missing_imports = true`.

Si quieres, puedo aplicar cambios automáticos sugeridos por ruff y corregir las anotaciones de tipo en `lag_transformer.py`.
