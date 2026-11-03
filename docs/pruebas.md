# Estrategia de pruebas

## Automáticas (`uv run pytest`)

56 tests que no necesitan Ollama ni red. El modelo se sustituye por un `FakeLLM` que devuelve
siempre los mismos hallazgos, de modo que se prueba la lógica propia, no al modelo.

| Fichero | Qué comprueba |
|---|---|
| `tests/test_diff.py` | Parseo del diff: líneas añadidas con su número correcto, ficheros borrados ignorados, diff vacío, numeración `L<n>`, clasificación código/test |
| `tests/test_graph.py` | Filtrado de hallazgos inventados, deduplicación y orden por gravedad, ejecución de los tres agentes, informe de un diff vacío sin llamar al modelo, aviso de «código sin tests» |
| `tests/test_diff_edge_cases.py` | Errores E1 y E2 de la revisión: marca `\ No newline at end of file`, línea añadida que empieza por `++ `, cabeceras falsas dentro de un hunk, recuentos incoherentes |
| `tests/test_agents.py` | Recorte sin dejar ficheros fuera (E3), diff delimitado como dato y delimitador inviolable (D1), fallo y reintento por agente (D3), rutas con prefijos (D5) |
| `tests/test_report.py` | Escape de menciones, enlaces, HTML y marca falsa (D1), informe honesto con ficheros omitidos o agentes caídos |
| `tests/test_cli.py` | `revisor review` con `--diff-file` y modelo falso, y los errores de uso |
| `tests/test_github.py` | El comentario se crea si no existe y se actualiza si ya existe (con `httpx.MockTransport`, sin red) |

`ci.yml` los ejecuta junto con `ruff` en cada push y PR.

## Prueba con modelo real

Se ejecutó el revisor contra `qwen2.5:7b-instruct` (Ollama en red interna) sobre
`examples/vulnerable.diff`, un diff inventado con tres problemas sembrados.

| Problema sembrado | ¿Detectado? | Gravedad | Línea |
|---|---|---|---|
| Clave de API escrita en el código | Sí | Alta | 3 |
| Inyección SQL por concatenación | Sí | Alta | 7 |
| Función con anidamiento excesivo | Sí | Media | 10 |
| Código sin tests | Sí (regla determinista) | Media | — |

Duración: unos 16 s para un diff pequeño.

### Lo que mostró la primera ejecución

Es útil dejarlo escrito, porque justifica las decisiones de diseño:

| Problema observado | Medida |
|---|---|
| Toda la salida con gravedad «baja» | El prompt define cuándo es alta, media o baja |
| Sin números de línea | El diff se le da con las líneas añadidas numeradas (`L<n>:`) |
| El agente de tests no avisaba de la falta de tests | Se calcula con una regla, sin depender del modelo |
| El mismo secreto lo reportaban tres agentes | Cada agente tiene prohibido revisar lo de los demás y el agregador deduplica por línea |
| El agente de tests inventó un hallazgo de seguridad | Su prompt se limita a pruebas |

## Prueba de inyección de prompts

Dos casos de la evaluación con `qwen2.5:7b-instruct` (ver [evaluacion.md](evaluacion.md)):
`adv01` (orden para callar un fallo real) **no** engañó al modelo; `adv02` (orden para inventar un
secreto crítico en código limpio) **sí**: los agentes de seguridad y de calidad lo informaron. La
versión anterior del revisor, sin defensas, también resistió `adv01`, así que la resistencia no se
debe a las defensas. Ver [amenazas.md](amenazas.md).

## Qué falta por probar

Esto **no** está verificado todavía y no debe afirmarse en la memoria hasta hacerlo:

- Ejecución real en GitHub Actions con un runner propio y un PR verdadero.
- Comportamiento con diffs grandes (recorte a 12 000 caracteres).
- Tasa de falsos positivos y falsos negativos con código real: haría falta un conjunto de PRs
  etiquetados a mano para medirla.
- Comparación entre modelos (`qwen3:8b`, `qwen3.5:9b`).

## Cómo añadir un caso nuevo

1. Guarda un diff representativo en `examples/` (sin código ni datos de la empresa).
2. Ejecuta `uv run revisor review --diff-file examples/<caso>.diff`.
3. Anota qué esperabas y qué salió. Si el modelo falla, ajusta el prompt y repite.
4. Si el fallo se puede evitar con una regla, añádela y cúbrela con un test.
