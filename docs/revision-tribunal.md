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
| D1 | **Hecho, con límites** | Diff delimitado como dato (`<diff>`), regla anti-inyección en los tres prompts, delimitador inviolable, y `escape_md` para todo texto del modelo (menciones, enlaces, HTML, marca oculta, longitud). Modelo de amenazas en `docs/amenazas.md`. **Límite:** la evaluación mostró que las defensas por prompt **no impiden** que un modelo fabrique un hallazgo por orden del código (caso `adv02`); ver `amenazas.md`. |
| D2 | **Hecho** | Cada agente tiene su propia escala de gravedad. En la prueba real se vio que el agente de calidad marcaba todo como «alta»; se acotó («ante la duda, la más baja»). |
| D3 | **Hecho** | Reintento por agente; si falla se conservan los hallazgos estáticos y el informe lo indica. Nunca dice «sin problemas» si algo falló u se omitió. |
| D4 | **Hecho** | Paginación por cabecera `Link` y filtro por autor (`github-actions[bot]`, configurable con `REVISOR_COMMENT_AUTHORS`). |
| D5 | **Hecho** | `normalize_path` quita `a/`, `b/`, `./`; los descartes se registran en el log. |
| D6 | **Hecho** | `uv sync --locked` en ambos workflows (`uv.lock` ya estaba en el repositorio). |
| D7 | **Hecho** | Un test por cada bug, tests de CLI con modelo falso y de recorte. Se renombró el test «…without_calling_the_model», que no comprobaba eso. |

Resultado: **74 tests** (con el arnés de evaluación) y `ruff` en verde (antes, 15).

## Bloqueantes

| Id | Estado | Qué se hizo y qué falta |
|---|---|---|
| B4 | **Hecho** | Leído el PDF oficial. Tabla criterio → evidencia en [requisitos-tfm.md](requisitos-tfm.md). **Hallazgo clave:** el PDF **no pide memoria**; pide README con 6 apartados, repositorio público, despliegue, slides, vídeo y formulario. README reescrito para seguir ese esquema. Además hay una contradicción de fechas (26/10 en el PDF frente a 30/11 en la lección) que debe aclarar el tutor. |
| B1 | **En curso** | Arnés, 29 casos, métricas, líneas base (Bandit, Ruff) y evaluación de tres modelos construidos; ver [evaluacion.md](evaluacion.md). Falta terminar la ejecución de los dos últimos modelos y analizar. Primer resultado (qwen2.5): exhaustividad alta, precisión baja, y el caso `adv02` demostró que la inyección de prompts **sí** funciona para fabricar hallazgos (corregido en `amenazas.md`). |
| B5 | **Pendiente** | Requiere publicar el repositorio y abrir PRs de demostración: lo hace el autor. Ver la advertencia sobre runners propios en repositorios públicos en [requisitos-tfm.md](requisitos-tfm.md). |
| B2 | **Parcial** | Memoria ampliada: resumen, objetivos, estado del arte, relación con el máster, diseño, metodología, resultados preliminares, seguridad, limitaciones, planificación, bibliografía. Faltan los resultados finales, las conclusiones y las fechas reales, que dependen del autor y de B1. Nota: el PDF no la exige. |
| B3 | **Parcial** | Sección 8 de la memoria reescrita con hechos: qué generó el asistente, qué decidió el autor, tabla de errores del asistente y quién los detectó, y cómo se verificó. **Lo que aporta el autor** (qué leyó y entiende, qué cambió, qué aprendió) está marcado como [COMPLETAR] y no puede rellenarlo nadie por él. |
