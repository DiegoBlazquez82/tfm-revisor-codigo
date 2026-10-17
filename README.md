# Revisor de código con agentes

Sistema multi-agente que revisa un pull request y publica un único comentario con los hallazgos
de seguridad (OWASP), calidad de código y pruebas. Trabajo Final de Máster del Máster en
Desarrollo con IA.

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

El informe ordena los hallazgos por gravedad, cita fichero y línea, y se actualiza en cada push
en lugar de añadir comentarios nuevos. Ejemplo de salida:

```
🔴 [Seguridad] Inyección SQL — `app/users.py`:7
La consulta SQL no utiliza parámetros parametrizados, lo que permite inyección SQL.

🟠 [Tests] Código modificado sin tests — `app/users.py`
```

## Inicio rápido

Requisitos: [uv](https://docs.astral.sh/uv/) (instala Python 3.11 si falta) y un servidor
[Ollama](https://ollama.com) con un modelo que admita salida estructurada.

```bash
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

### Configuración

| Variable | Por defecto | Uso |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Servidor Ollama |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct` | Modelo de los tres agentes |
| `GITHUB_TOKEN` | — | Solo con `--repo`/`--pr`; en Actions lo aporta GitHub |

## Documentación

- [Arquitectura](docs/arquitectura.md): componentes, decisiones de diseño y límites.
- [Despliegue](docs/despliegue.md): runner propio, variables, seguridad y problemas frecuentes.
- [Pruebas](docs/pruebas.md): estrategia, prueba con modelo real y qué falta por verificar.
- [Memoria del TFM](docs/memoria-tfm.md): borrador para la entrega, con las partes que debes
  completar tú.

## Integración continua

- `.github/workflows/ci.yml`: lint (ruff) y tests en cada push y PR.
- `.github/workflows/pr-review.yml`: ejecuta el revisor en cada PR del propio repositorio, con
  permisos mínimos, en un runner propio con la etiqueta `ollama`.

## Seguridad

- Permisos mínimos en los workflows (`contents: read`, `pull-requests: write`).
- No se ejecuta código del PR: solo se lee el diff como texto.
- El token llega por variable de entorno; nunca está en el código.
- La salida del modelo se valida con Pydantic y se filtra antes de publicarse.
- Los PRs de forks no se revisan automáticamente.

## Limitaciones

- El diff se recorta a ~12 000 caracteres por agente; el informe lo indica.
- Un modelo local de 7B genera falsos positivos y se le escapan casos. Es una ayuda a la revisión
  humana, no un sustituto.
- Cada agente ve solo el diff, no el repositorio completo.

## Estructura

```
src/revisor/    código (diff, agentes, grafo, informe, cliente de GitHub, CLI)
tests/          tests automáticos (sin red ni modelo)
examples/       diffs de ejemplo
docs/           documentación
.github/        workflows de CI y de revisión de PR
```
