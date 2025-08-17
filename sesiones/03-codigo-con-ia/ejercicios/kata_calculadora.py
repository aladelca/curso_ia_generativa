#!/usr/bin/env python3

def calcular(expr: str) -> float:
    """Implementa una calculadora básica que soporte +, -, *, / y paréntesis.
    Requisitos: espacios opcionales, números decimales, precedencia correcta.
    """
    raise NotImplementedError


if __name__ == "__main__":
    ejemplos = [
        "1 + 2*3",
        "(2 + 3) * 4 - 5 / 2",
        "10 / (5 - 3) + 7",
    ]
    for e in ejemplos:
        print(e, "=>", calcular(e))
