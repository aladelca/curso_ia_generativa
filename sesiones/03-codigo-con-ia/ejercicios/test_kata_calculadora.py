import math
import pytest

from .kata_calculadora import calcular


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
def test_expresiones_validas(expr: str, expected: float) -> None:
    assert math.isclose(calcular(expr), expected, rel_tol=1e-9, abs_tol=0.0)


@pytest.mark.parametrize(
    "expr",
    [
        "",  # vacío
        "(1+2",  # paréntesis desbalanceados
        "2//3",  # operador no soportado
        "a + 1",  # caracteres inválidos
    ],
)
def test_expresiones_invalidas(expr: str) -> None:
    with pytest.raises(ValueError):
        calcular(expr)


def test_division_por_cero() -> None:
    with pytest.raises(ZeroDivisionError):
        calcular("1/0")



