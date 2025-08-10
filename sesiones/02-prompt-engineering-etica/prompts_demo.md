# Prompts de demostración — Sesión 2

Guía de 20 prompts (5 versiones × 4 tareas) para demo en vivo. Estructura gradual: general → específico → con formato.

---

## 1) Resúmenes

1. General:
   - Resume el siguiente texto.

2. Con objetivo y audiencia:
   - Resume el siguiente texto para ejecutivos no técnicos en 5–7 líneas.

3. Con restricciones de estilo y longitud:
   - Resume en 5 viñetas de no más de 12 palabras cada una; evita jerga.

4. Rol y checklist:
   - Actúa como editor técnico. Resume para un CTO. Si hay jerga, defínela en una frase.

5. Formato validable (JSON):
   - Resume el texto y responde SOLO con JSON válido con la forma:
     {"resumen":"string","puntos_clave":["string"],"riesgos":["string"],"confianza":0.0}

---

## 2) Análisis

1. General:
   - ¿Cuáles son los pros y contras del enfoque descrito?

2. Con criterios:
   - Analiza pros y contras considerando costo, tiempo y riesgo operativo.

3. Con evidencia:
   - Lista pros/contras y cita evidencia textual entre comillas.

4. Con rol y límites:
   - Eres auditor de procesos. Evalúa impacto en cumplimiento normativo en 120–150 palabras.

5. Formato validable (JSON):
   - Devuelve SOLO JSON con: {"pros":[""],"contras":[""],"evidencia":[""],"recomendacion":""}

---

## 3) Código

1. General:
   - Escribe una función en Python que calcule la mediana de una lista.

2. Con firma y pruebas breves:
   - Implementa `def median(values: list[float]) -> float:` y pasa casos: [], [1], [1,2,3], [1,2]. Define comportamiento para lista vacía.

3. Con complejidad y errores:
   - Maneja entradas no numéricas con `TypeError`. Complejidad O(n log n) o mejor.

4. Con documentación y estilo:
   - Incluye docstring clara, type hints, y pruebas rápidas bajo `if __name__ == "__main__":`.

5. Con formato de salida (snippet JSON para test):
   - Responde con JSON: {"code":"<python>","tests":[{"input":[1,2,3],"expected":2}]}

---

## 4) Preguntas random (con propósito didáctico)

1. General:
   - Dame ideas para un nombre de app de hábitos.

2. Con criterios y tono:
   - 10 nombres cortos, tono optimista, disponibles como .app hipotéticamente.

3. Con público y restricciones:
   - Público: bilingüe ES/EN. Evita palabras comunes como "habit" o "rutina".

4. Con evaluación propia:
   - Devuelve 10 opciones y auto‑puntúa originalidad 1–5 con breve justificación.

5. Formato validable (tabla Markdown):
   - Devuelve una tabla con columnas: nombre | razon | originalidad(1–5).

---

## Sugerencias de uso en vivo

- Mostrar la diferencia entre versiones cambiando UNA variable a la vez.
- Validar JSON pegándolo en un validador o con `json.loads` en Python.
- Comparar resultados con `ejercicios/ex_prompt_eval.py` cuando aplique.


