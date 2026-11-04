# Revisor de código con agentes

Trabajo Final de Máster — Máster en Desarrollo con IA (BIG School).

## 1. Descripción general

Sistema multi-agente que revisa automáticamente un *pull request* y publica **un único comentario**
con los hallazgos de **seguridad (OWASP Top 10)**, **calidad de código** y **pruebas**.

La revisión de código es un cuello de botella y los revisores humanos pasan por alto cuestiones
repetitivas (secretos escritos en el código, inyecciones, falta de tests). Este proyecto ofrece una
primera revisión rápida y consistente que ayuda al revisor humano, **sin sustituirlo**. Se ejecuta en
GitHub Actions con un modelo de lenguaje **local** (Ollama), de modo que el código no sale de la red.

Un grafo de [LangGraph](https://langchain-ai.github.io/langgraph/) lanza tres agentes en paralelo
sobre el diff del PR y un agregador junta sus resultados:

```
diff del PR ──► security ─┐
            ├─► smells   ─┼─► aggregate ──► comentario en el PR
            └─► tests    ─┘
```

Ejemplo de salida:

```
🔴 [Seguridad] Inyección SQL — `app/users.py`:7
La función `find_user` concatena el parámetro `name` en la consulta SQL.

🟠 [Tests] Código modificado sin tests — `app/users.py`
```

## 2. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.11 |
| Orquestación de agentes | [LangGraph](https://langchain-ai.github.io/langgraph/) |
| Modelo de lenguaje | [Ollama](https://ollama.com) con `qwen2.5:7b-instruct` (vía `langchain-ollama`) |
| Validación de la salida | Pydantic |
| API de GitHub | httpx |
| Gestión del proyecto | [uv](https://docs.astral.sh/uv/) |
| Pruebas y calidad | pytest, ruff |
| Integración continua | GitHub Actions |
| Evaluación (solo desarrollo) | Bandit, Ruff como líneas base |

## 3. Instalación y ejecución

Requisitos: [uv](https://docs.astral.sh/uv/) (instala Python 3.11 si falta) y un servidor Ollama con
un modelo que admita salida estructurada (`ollama pull qwen2.5:7b-instruct`).

```bash
git clone https://github.com/DiegoBlazquez82/tfm-revisor-codigo.git
cd tfm-revisor-codigo
uv sync

uv run pytest                  # no necesita Ollama: los tests usan un modelo falso
uv run ruff check .

# Revisar un diff de ejemplo contra tu Ollama
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=qwen2.5:7b-instruct
uv run revisor review --diff-file examples/vulnerable.diff

# Revisar un PR real y comentar en él (GITHUB_TOKEN con pull-requests: write)
uv run revisor review --repo owner/repo --pr 12 --post
```

| Variable | Por defecto | Uso |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Servidor Ollama |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct` | Modelo de los tres agentes |
| `GITHUB_TOKEN` | — | Solo con `--repo`/`--pr`; en Actions lo aporta GitHub |
| `REVISOR_COMMENT_AUTHORS` | `github-actions[bot]` | Autores cuyo comentario se actualiza |

Para ejecutarlo en cada PR hay que registrar un runner propio con la etiqueta `ollama`; ver
[docs/despliegue.md](docs/despliegue.md).

## 4. Estructura del proyecto

```
src/revisor/              código del revisor
  cli.py                  línea de comandos (`revisor review ...`)
  graph.py                grafo LangGraph: tres agentes en paralelo + agregador
  agents.py               prompts y fábrica de los agentes
  diff.py                 parseo del diff y numeración de líneas
  models.py               esquemas Pydantic de los hallazgos
  report.py               deduplicación, orden y comentario en Markdown
  github.py               cliente de la API de GitHub (leer diff, comentar)
  evaluation/             arnés de evaluación (casos, puntuación, líneas base)
tests/                    tests automáticos (sin red ni modelo)
examples/                 diffs de ejemplo (uno con inyección de prompts)
eval/                     casos exportados y resultados de la evaluación
docs/                     documentación
.github/workflows/        CI y revisión automática de PRs
```

## 5. Funcionalidades principales

- **Revisión de seguridad** según OWASP Top 10 y detección de secretos escritos en el código.
- **Revisión de calidad**: code smells (anidamiento, funciones largas, números mágicos, duplicación…).
- **Revisión de pruebas**: tests sin aserciones, dependencias externas sin aislar y aviso
  determinista de «código modificado sin tests».
- **Informe único y limpio**: hallazgos ordenados por gravedad, con fichero y línea, deduplicados.
  Se actualiza en cada push en vez de añadir comentarios nuevos.
- **Robusto**: si un agente falla, el informe lo dice y no afirma que todo esté bien; los diffs
  grandes se recortan y se lista qué no se revisó.
- **Seguro**: se ejecuta desde la rama base del repositorio, trata el contenido del PR como no
  confiable y escapa todo lo que publica. Ver [docs/amenazas.md](docs/amenazas.md).
- **Evaluado**: 29 casos etiquetados, comparación con Bandit y Ruff y entre tres modelos. Ver
  [docs/evaluacion.md](docs/evaluacion.md).

## 6. Usuario y contraseña de prueba

**No aplica**: el proyecto no tiene login. Es una herramienta de línea de comandos y un workflow de
GitHub Actions.

## Enlaces de la entrega

| Entregable | Enlace |
|---|---|
| Repositorio público de GitHub | https://github.com/DiegoBlazquez82/tfm-revisor-codigo |
| Despliegue / acceso al proyecto en funcionamiento | **[PENDIENTE: URL de un PR con el comentario del revisor]** |
| Slides de la presentación | **[PENDIENTE: URL]** |
| Vídeo (explicación con captura de pantalla) | **[PENDIENTE: URL]** |

## Documentación

- [Arquitectura](docs/arquitectura.md): componentes, decisiones de diseño y límites.
- [Modelo de amenazas](docs/amenazas.md): qué se asume, qué puede fallar y qué no está cubierto.
- [Despliegue](docs/despliegue.md): runner propio, variables, seguridad y problemas frecuentes.
- [Pruebas](docs/pruebas.md): estrategia de tests y pruebas con modelo real.
- [Evaluación](docs/evaluacion.md) y [resultados](docs/evaluacion-resultados.md): metodología y cifras.
- [Requisitos del TFM](docs/requisitos-tfm.md): qué pide el máster y dónde se cumple.
- [Memoria](docs/memoria-tfm.md): estado del arte, decisiones, resultados y uso de IA.
- [Registro de la revisión](docs/revision-tribunal.md): estado de cada punto de la revisión.

## Limitaciones

- El diff se recorta a ~12 000 caracteres por agente; el informe lo indica.
- Un modelo local de 7B genera falsos positivos y se le escapan casos. Es una ayuda a la revisión
  humana, no un sustituto.
- Cada agente ve solo el diff, no el repositorio completo.
- La defensa frente a inyección de prompts es parcial (ver [docs/amenazas.md](docs/amenazas.md)).

## Uso de IA en el desarrollo

El código, los tests y la documentación se desarrollaron con ayuda de un asistente de IA (Claude
Code). Qué decisiones tomó el autor, qué generó el asistente y cómo se revisó está en la sección 8
de la [memoria](docs/memoria-tfm.md#8-uso-de-ia-y-autoría).
