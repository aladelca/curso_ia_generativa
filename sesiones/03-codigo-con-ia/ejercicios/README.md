# Ejercicios — Sesión 3

- Caso 1: Completar `kata_calculadora.py` con TDD.
- Caso 2: Pedir al asistente explicar y documentar la solución.
- Caso 3: Generar tests adicionales (edge cases).

## Objetivo
Implementar una calculadora por expresiones con cobertura de pruebas, documentación clara y calidad estática (tipos y lint).

## Requisitos mínimos
- Implementa `calcular(expr: str) -> float` respetando precedencia y paréntesis.
- Lanza `ValueError` ante entradas inválidas.
- Añade docstrings estilo Google y `type hints`.

## Tests (pytest)
Ejecutar:

```
pytest -q sesiones/03-codigo-con-ia/ejercicios
```

Empieza por los casos en `test_kata_calculadora.py` y añade más (vacío, división por cero, espacios, decimales, anidación).

## Calidad estática
Comandos sugeridos:

```
mypy sesiones/03-codigo-con-ia/ejercicios
flake8 sesiones/03-codigo-con-ia/ejercicios
ruff check sesiones/03-codigo-con-ia/ejercicios
```

Tip: corrige primero errores de tipos, luego lint. Mantén funciones pequeñas y puras.

## Guía de docstrings (estilo Google)
Describe propósito, argumentos, retorno y errores. Incluye un ejemplo corto de uso cuando sea útil.
