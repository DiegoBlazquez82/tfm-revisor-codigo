# Registro de la revisión del tribunal (3 nov 2026)

Revisión hecha sobre el commit `00ddd29`. Aquí se anota el estado real de cada punto y lo que se hizo.
Las correcciones de código están en el commit que acompaña a este fichero.

> Sobre la autoría (B3): los errores E1–E4 y los puntos D1–D7 **los detectó la revisión externa**, no
> el desarrollo. Lo correcto en la memoria es decirlo así: la revisión los encontró, se
> reprodujeron, se corrigieron y se cubrieron con tests.

## Errores confirmados

| Id | Estado | Qué se hizo |
|---|---|---|
| E1 | **Hecho** | `parse_diff` y `annotate_patch` ignoran las líneas que empiezan por `\`. Tests en `tests/test_diff_edge_cases.py`; comprobado que fallan con el código anterior. |
| E2 | **Hecho** | El parser usa los recuentos de la cabecera `@@` para saber cuándo termina un hunk: dentro de él, `+++ …` es una línea añadida, no un fichero. Cubre también la línea eliminada `--- …`. Un `diff --git` cierra siempre el hunk, aunque los recuentos sean incoherentes. |
| E3 | **Hecho** | `render_diff` ya no corta en el primer bloque que no cabe: entran primero los ficheros que caben y el resto se recorta. Devuelve la lista de ficheros omitidos o recortados y el informe la muestra. |
| E4 | **Hecho** | El workflow pasa a `pull_request_target`: workflow y revisor salen de la rama **base**, sin checkout de la del PR. Texto corregido en README, `docs/despliegue.md` y memoria (§2 y §7). Se documenta como incidencia en `docs/amenazas.md` (A1). Detalle que la revisión no mencionaba: con `pull_request`, el propio fichero del workflow se toma de la rama del PR, así que checkout de la base por sí solo no habría bastado. |

## Diseño y calidad

| Id | Estado | Qué se hizo |
|---|---|---|
| D1 | **Hecho, con límites** | Diff delimitado como dato (`<diff>`), regla anti-inyección en los tres prompts, delimitador inviolable, y `escape_md` para todo texto del modelo (menciones, enlaces, HTML, marca oculta, longitud). Modelo de amenazas en `docs/amenazas.md`. **Límite:** la prueba con `examples/prompt-injection.diff` no demostró que las defensas sean la causa de la resistencia (la versión anterior tampoco obedeció). |
| D2 | **Hecho** | Cada agente tiene su propia escala de gravedad. En la prueba real se vio que el agente de calidad marcaba todo como «alta»; se acotó («ante la duda, la más baja»). |
| D3 | **Hecho** | Reintento por agente; si falla se conservan los hallazgos estáticos y el informe lo indica. Nunca dice «sin problemas» si algo falló u se omitió. |
| D4 | **Hecho** | Paginación por cabecera `Link` y filtro por autor (`github-actions[bot]`, configurable con `REVISOR_COMMENT_AUTHORS`). |
| D5 | **Hecho** | `normalize_path` quita `a/`, `b/`, `./`; los descartes se registran en el log. |
| D6 | **Hecho** | `uv sync --locked` en ambos workflows (`uv.lock` ya estaba en el repositorio). |
| D7 | **Hecho** | Un test por cada bug, tests de CLI con modelo falso y de recorte. Se renombró el test «…without_calling_the_model», que no comprobaba eso. |

Resultado: **56 tests** y `ruff` en verde (antes, 15).

## Bloqueantes: siguen abiertos

| Id | Estado | Por qué |
|---|---|---|
| B4 | **Pendiente** | El PDF de criterios sigue sin leerse (el navegador lo trató como descarga). Hay que guardarlo en el proyecto o pegar sus requisitos. |
| B1 | **Pendiente** | No existe todavía el conjunto de diffs etiquetados ni la comparación con Semgrep/Bandit y entre modelos. Solo hay dos diffs de ejemplo. Es el trabajo más grande que queda. |
| B5 | **Pendiente** | Requiere publicar el repositorio, registrar el runner con la etiqueta `ollama` y abrir PRs reales: lo hace el autor. |
| B2 | **Pendiente** | La memoria sigue siendo un borrador; faltan estado del arte, metodología, planificación, resultados reales, conclusiones y bibliografía. |
| B3 | **Pendiente** | La sección debe reflejar el trabajo real del autor. Ver la nota de arriba sobre quién detectó cada error. |
