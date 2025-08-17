# Guía práctica — Tests, tipos y estándares con IA (Sesión 3)

Contenido práctico para pytest, mypy, flake8, ruff y prompts útiles de IA.

---

## 1) Pruebas con pytest

- Escribe tests antes y después de refactorizar (TDD cuando sea posible)
- Cubre: casos nominales, bordes y errores esperados
- Mantén los tests rápidos y deterministas

Ejemplo de tests para `calcular(expr: str) -> float`:

```python
import math
import pytest
from sesiones.03-codigo-con-ia.ejercicios.kata_calculadora import calcular

@pytest.mark.parametrize(
    "expr,expected",
    [
        ("1+2", 3.0),
        ("1 + 2*3", 7.0),
        ("(2+3)*4 - 5/2", (2 + 3) * 4 - 5 / 2),
        ("10 / (5 - 3) + 7", 10 / (5 - 3) + 7),
        ("3.5 * 2", 7.0),
        ("(1 + (2*3))", 7.0),
    ],
)
def test_validas(expr: str, expected: float) -> None:
    assert math.isclose(calcular(expr), expected, rel_tol=1e-9)

@pytest.mark.parametrize("expr", ["", "(1+2", "2//3", "a + 1"])
def test_invalidas(expr: str) -> None:
    with pytest.raises(ValueError):
        calcular(expr)

def test_division_por_cero() -> None:
    with pytest.raises(ZeroDivisionError):
        calcular("1/0")
```

Comandos:

```bash
pytest -q
pytest -q -k calcular
pytest -q --maxfail=1 --disable-warnings
```

---

## 2) Tipado estático con mypy

- Añade `type hints` a funciones públicas y módulos core
- Evita `Any`; usa `Optional`, `Union` y genéricos cuando corresponda
- mypy detecta `None`, incompatibilidades y rutas de ejecución no tipadas

Docstring y tipos (estilo Google):

```python
def calcular(expr: str) -> float:
    """Evalúa una expresión aritmética simple.

    Args:
        expr: Expresión con +, -, *, / y paréntesis.

    Returns:
        Resultado como `float`.

    Raises:
        ValueError: Si la expresión es inválida.
    """
    ...
```

Manejo correcto de `Optional`:

```python
from typing import Optional

def parsear_numero(texto: str) -> Optional[float]:
    try:
        return float(texto)
    except ValueError:
        return None

num = parsear_numero("3.14")
if num is None:
    raise ValueError("Número inválido")
valor: float = num
```

Comando:

```bash
mypy sesiones/03-codigo-con-ia/ejercicios
```

---

## 3) Estilo y calidad con flake8 y ruff

- flake8: PEP 8 y errores comunes
- ruff: linting/format rápido; puede sustituir a varios plugins

Comandos:

```bash
flake8 sesiones/03-codigo-con-ia/ejercicios
ruff check sesiones/03-codigo-con-ia/ejercicios
```

Antes vs. después:

```python
# Antes (import no usado, one-liner, nombres pobres)
import math
def f(a, b): return a+b  # noqa: E701

# Después
from typing import Union

def sumar(n1: Union[int, float], n2: Union[int, float]) -> float:
    """Suma dos números y devuelve float."""
    return float(n1) + float(n2)
```

---

## 4) Configuraciones mínimas

`.flake8`:

```ini
[flake8]
max-line-length = 100
extend-ignore = E203, W503
per-file-ignores = __init__.py:F401
```

`pyproject.toml` (ruff y mypy):

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "B", "I", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.10"
warn_unused_ignores = true
warn_return_any = true
no_implicit_optional = true
strict_equality = true
check_untyped_defs = true
disallow_untyped_defs = true
```

`pytest.ini` (opcional):

```ini
[pytest]
addopts = -q --maxfail=1 --disable-warnings
```

---

## 5) Prompts útiles para IA asistente (IAA)

- Generar tests:
  - "Genera 10 tests con pytest para `calcular`, cubriendo casos borde (vacío, paréntesis anidados, decimales, división por cero) y errores (caracteres inválidos). Usa `parametrize` y `pytest.raises`."
- Añadir docstrings/tipos:
  - "Añade docstrings estilo Google y type hints a estas funciones sin cambiar la lógica. Incluye `Raises`."
- Mejorar calidad:
  - "Refactoriza para reducir complejidad cognitiva <10, evita one‑liners y separa I/O de la lógica."
- Resolver mypy:
  - "Corrige estos errores de mypy manteniendo el contrato público. Evita `Any` y maneja `Optional` explícitamente."
- Ajustar linters:
  - "Propón cambios para pasar ruff y flake8 con `line-length=100`, sin desactivar reglas críticas."

---

## 6) Pipeline de verificación (manual)

```bash
# 1. Tests
pytest -q

# 2. Tipos
mypy sesiones/03-codigo-con-ia/ejercicios

# 3. Linter
ruff check sesiones/03-codigo-con-ia/ejercicios
flake8 sesiones/03-codigo-con-ia/ejercicios
```

Checklist final:
- Tests pasan (pytest)
- Tipos ok (mypy)
- Linter ok (ruff/flake8)
- Docstrings presentes y actualizadas


