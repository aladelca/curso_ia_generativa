# Ejercicios — Sesión 2

## Caso 1 — Reescritura con control de tono y estilo
- Objetivo: transformar un texto preservando el significado y ajustando tono/audiencia.
- Ciclos: 3 iteraciones (zero‑shot → con restricciones → con checklist de evaluación).

Indicaciones:
1) Pega un párrafo técnico de ~150–200 palabras.
2) Define audiencia (ej.: ejecutivos no técnicos) y tono (claro, directo, no hype).
3) Pide salida en viñetas y límite de 120 palabras.
4) Añade checklist: “verifica que no haya jerga; si hay, explica en una frase”.

## Caso 2 — Prompt con formato JSON validable (Schema‑first)
- Objetivo: obtener respuestas estructuradas y fáciles de evaluar.
- Esquema mínimo esperado:

```json
{
  "resumen": "string",
  "puntos_clave": ["string"],
  "riesgos": ["string"],
  "confianza": 0.0
}
```

Indicaciones:
- Define campos obligatorios, tipos y límites de longitud.
- Pide “responder SOLO con JSON válido”.
- Valida sintaxis JSON con cualquier validador o cargando en Python.

## Caso 3 — Evaluación automática de calidad (Python)
- Objetivo: medir precisión, cobertura, estructura y adecuación.
- Archivos requeridos: `respuestas.txt` y `oro.txt` (una respuesta por línea).
- Opcional: `requisitos.txt` con palabras/expresiones obligatorias por línea.

Comando básico:

```
python ex_prompt_eval.py --pred respuestas.txt --gold oro.txt
```

Con requisitos y reporte CSV:

```
python ex_prompt_eval.py --pred respuestas.txt --gold oro.txt \
  --required requisitos.txt --csv reporte.csv
```

Métricas reportadas:
- F1 léxico (aproximado), cobertura vs. verdad, precisión léxica
- Estructura (JSON válido/opcional terminación correcta)
- Adecuación (longitud y presencia de requisitos)

Sugerencias:
- Itera cambios pequeños al prompt y re‑evalúa.
- Usa variantes de few‑shot representativas y diversas.
