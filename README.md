# Revisor de código con agentes

Sistema multi-agente que revisa un pull request y publica un único comentario con los hallazgos.
TFM del Máster en Desarrollo con IA.

## Qué hace

Un grafo de [LangGraph](https://langchain-ai.github.io/langgraph/) lanza tres agentes en paralelo
sobre el diff del PR y un agregador junta sus resultados:

| Agente | Revisa |
|---|---|
| `security` | OWASP Top 10 y secretos en el código |
| `smells` | Code smells y mantenibilidad |
| `tests` | Cobertura del cambio y calidad de las pruebas |

```
diff del PR ──► security ─┐
            ├─► smells   ─┼─► aggregate ──► comentario en el PR
            └─► tests    ─┘
```

El agregador elimina duplicados, ordena por gravedad y descarta los hallazgos que el modelo se
inventa sobre ficheros que no están en el diff. El comentario se actualiza en cada push (lleva una
marca oculta), así que no llena el PR de mensajes.

## Uso local

Requisitos: Python 3.11+, [uv](https://docs.astral.sh/uv/) y [Ollama](https://ollama.com) con un
modelo de código (`ollama pull qwen2.5-coder:7b`).

```bash
uv sync
uv run pytest                                   # no necesita Ollama: los tests usan un modelo falso
uv run revisor review --diff-file cambio.diff   # imprime el informe

# Contra un PR real (publica el comentario)
export GITHUB_TOKEN=...   # con permiso pull-requests: write
uv run revisor review --repo owner/repo --pr 12 --post
```

Variables: `OLLAMA_MODEL` (por defecto `qwen2.5-coder:7b`), `OLLAMA_BASE_URL`
(por defecto `http://localhost:11434`).

## Integración con GitHub Actions

- `.github/workflows/ci.yml`: lint (ruff) y tests en cada push y PR.
- `.github/workflows/pr-review.yml`: ejecuta el revisor en cada PR. Corre en un runner propio con la
  etiqueta `ollama`, porque el modelo es local. Solo se ejecuta en PRs del mismo repositorio.

## Decisiones de seguridad

- Permisos mínimos en los workflows (`contents: read`, `pull-requests: write`).
- No se ejecuta código del PR: el revisor solo lee el diff como texto.
- El token se pasa por variable de entorno desde `secrets.GITHUB_TOKEN`; nunca se escribe en código.
- La salida del modelo se valida con Pydantic y se filtra antes de publicarla.
- El prompt trata el diff como datos a analizar, no como instrucciones; aun así, el comentario avisa
  de que es generado por IA y debe revisarse.

## Limitaciones conocidas

- El diff se recorta a ~12 000 caracteres por agente; los PR enormes se revisan solo en parte.
- Un modelo local pequeño produce falsos positivos y se le escapan cosas: es una ayuda a la
  revisión humana, no un sustituto.

## Uso de IA en el desarrollo

_Completar antes de la entrega: qué herramientas usaste, qué partes generó la IA y cómo las
revisaste y probaste._
