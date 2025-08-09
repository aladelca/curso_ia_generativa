# CIIP — IA Generativa y Automatización Inteligente

Este repositorio contiene el material de clase organizado por sesión:
- Diapositivas en Markdown
- Ejercicios prácticos en Python
- Datos de ejemplo cuando aplica

## Uso de las diapositivas

Las diapositivas están preparadas para Marp.
- Ver en VS Code con la extensión «Marp for VS Code» o exportar a PDF/HTML.
- Cada `slides.md` incluye front‑matter y estilos en fondo negro.

## Entorno de trabajo

1) Crear y activar un entorno virtual (opcional):
```
python3 -m venv .venv
source .venv/bin/activate
```
2) Instalar dependencias:
```
pip install -r requirements.txt
```
3) Variables opcionales (para API de OpenAI):
- Crear un archivo `.env` en la raíz con:
```
OPENAI_API_KEY=tu_api_key
```

## Estructura

```
sesiones/
  01-que-es-un-llm/
  02-prompt-engineering-etica/
  03-codigo-con-ia/
  03b-integracion-entornos/
  04-exploracion-datos-ia/
  05-visualizacion-ia/
  06-insights-reportes/
  07-nl-a-sql/
  08-proyecto-asistente-sql/
  09-openai-api-langchain/
  10-agentes-copilotos/
```

## Nota
Los ejercicios están pensados para correr en macOS/Linux con Python 3.10+.
