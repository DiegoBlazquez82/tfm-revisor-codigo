# Memoria del TFM — Revisor de código con agentes

> **Estado del documento.** Borrador escrito solo con hechos verificados en el repositorio. Las
> partes marcadas **[COMPLETAR]** dependen del autor (experiencia propia, decisiones, resultados que
> aún no existen). El PDF oficial del máster **no exige una memoria**: pide README, repositorio
> público, despliegue, slides y vídeo (ver [requisitos-tfm.md](requisitos-tfm.md)). Este documento
> es un complemento para defender el trabajo.

## 1. Resumen

Sistema que, al abrirse un pull request, analiza su diff con tres agentes de IA especializados
(seguridad según OWASP Top 10, code smells y pruebas), unifica los resultados y los publica como un
único comentario en el propio PR. Se orquesta con LangGraph, se ejecuta en GitHub Actions y usa un
modelo de lenguaje local (Ollama), de modo que el código no sale de la red de la organización.

Se evaluó con 29 casos etiquetados, comparándolo con dos analizadores estáticos (Bandit y Ruff) y
entre tres modelos. **Resultado principal:** el modelo encuentra la mayoría de los problemas reales
(exhaustividad alta) pero produce muchos falsos positivos (precisión baja), también en código
correcto; ver el apartado 7. El proyecto se presenta como ayuda a la revisión humana, no como
sustituto.

## 2. Problema y objetivos

**Problema.** La revisión de código es un cuello de botella y los revisores pasan por alto
cuestiones repetitivas: secretos escritos en el código, inyecciones, falta de pruebas.

**Objetivo general.** Ofrecer una primera revisión automática, rápida y consistente que ayude al
revisor humano.

**Objetivos específicos**
1. Detectar problemas de seguridad del OWASP Top 10 en el código añadido.
2. Señalar code smells que perjudican el mantenimiento.
3. Avisar cuando un cambio de código no trae pruebas o las trae débiles.
4. Integrarlo en GitHub Actions sin ejecutar código del PR: el revisor corre desde la rama base.
5. Mantener el código dentro de la red mediante un modelo local.
6. **Medir** su calidad frente a una línea base, en lugar de suponerla.

**Fuera de alcance:** corregir el código automáticamente, sustituir la revisión humana, analizar el
repositorio completo, soportar otros lenguajes distintos de los casos evaluados (Python).

## 3. Estado del arte

La revisión automática de código se aborda desde dos familias de herramientas.

**Análisis estático basado en reglas.** Detectan patrones conocidos de forma determinista, rápida y
barata, con pocos falsos positivos en lo que cubren, pero no entienden el contexto ni detectan lo que
no está en sus reglas.
- *Bandit*: analizador de seguridad para Python.
- *Ruff*: linter con reglas de complejidad, estilo y errores frecuentes.
- *Semgrep*: búsqueda de patrones de código con reglas personalizables.
- *SonarQube*: plataforma de calidad y seguridad de código.

**Revisión asistida por modelos de lenguaje.** Leen el cambio y redactan comentarios en lenguaje
natural, con capacidad de razonar sobre el contexto, a cambio de variabilidad, coste y falsos
positivos.
- *CodeRabbit* y *GitHub Copilot code review*: servicios que comentan PRs con IA; ambos se vieron en
  el máster.
- *PR-Agent*: proyecto de código abierto que revisa PRs con un LLM.

**Riesgos específicos de usar un LLM sobre código ajeno.** El código que revisa lo escribe un
tercero, así que puede contener instrucciones dirigidas al modelo. La inyección de prompts figura
entre los riesgos principales de las aplicaciones con LLM (OWASP Top 10 for LLM Applications).

**Posicionamiento de este trabajo.** No pretende competir con los productos anteriores, que no se han
probado aquí. Aporta: modelo local (el código no sale de la red), arquitectura abierta de tres
agentes, endurecimiento de la ejecución en CI (ver [amenazas.md](amenazas.md)) y, sobre todo, una
**evaluación con línea base** que mide cuánto aporta el modelo frente a analizadores estáticos
gratuitos.

> **[COMPLETAR]** Si se quiere ampliar, consultar la documentación actual de cada herramienta y
> citarla con fecha de consulta; aquí solo se recogen sus rasgos generales, no comparativas de
> precisión.

## 4. Relación con los contenidos del máster

| Parte del proyecto | Módulos del máster |
|---|---|
| Grafo de agentes en paralelo con LangGraph | LangChain con Python, Multi-agents |
| Salida estructurada validada con Pydantic | LangChain con Python, Prompt engineering para developers |
| Modelo local con Ollama | Modelos de IA locales |
| Revisión OWASP, secretos, permisos mínimos | Seguridad (OWASP Top 10, desarrollo seguro) |
| Workflows de CI y de revisión | DevOps y CI/CD, Copilot dentro de GitHub |
| Tests automáticos con modelo simulado | Testing |
| Code smells como criterio de revisión | Code smells, refactor y deuda; Métricas |
| Evaluación con LLM-as-a-judge / métricas | LLMOps |
| Documentación del proyecto | Documentación con IA |

## 5. Diseño

Detalle en [arquitectura.md](arquitectura.md). Resumen: tres agentes en paralelo (`security`,
`smells`, `tests`) con un prompt por criterio; un agregador que deduplica y ordena; un cliente de
GitHub que crea o actualiza un único comentario.

Decisiones destacables:
- Un criterio por agente, con la indicación explícita de qué *no* revisar.
- La salida del modelo se trata como no fiable: se valida, se filtra, se deduplica y se escapa.
- Lo que puede decidirse con reglas (código sin tests) no se delega en el modelo.
- Un agente que falla no tumba la revisión, y el informe nunca afirma «sin problemas» si algo falló.
- El workflow se ejecuta desde la rama base (`pull_request_target`).

## 6. Metodología de evaluación

Detalle en [evaluacion.md](evaluacion.md). 29 casos sintéticos (10 de seguridad, 6 de calidad, 3 de
pruebas, 8 limpios y 2 adversariales) con 21 etiquetas, generadas a partir de marcas en el código
fuente. Métricas por agente y del informe final: precisión, exhaustividad, F1, falsos positivos en
casos limpios y tiempo. Líneas base: Bandit (seguridad) y Ruff (calidad). Tres modelos: `qwen2.5:7b-instruct`,
`qwen3:8b` y `qwen3.5:9b`.

**Limitaciones:** pocos casos (diferencias pequeñas no son significativas), etiquetas escritas por un
solo etiquetador que no es humano, código más fácil que el real y solo Python.

## 7. Resultados

Cifras completas en [evaluacion-resultados.md](evaluacion-resultados.md).

> **[COMPLETAR cuando termine la evaluación]** Tabla resumen por modelo y agente, comparación con
> Bandit y Ruff, falsos positivos en casos limpios, tiempos y lectura de los resultados.

Observaciones ya verificadas con `qwen2.5:7b-instruct` (primer modelo evaluado):
- **Alta exhaustividad, baja precisión.** Encuentra casi todo lo etiquetado, pero añade muchos
  hallazgos que no lo están. En código correcto que *parece* peligroso (SQL parametrizado,
  `subprocess` con lista de argumentos y validación, token tomado del entorno) reportó inyección SQL,
  inyección de comandos y «secretos en el código». Es decir, reacciona a patrones superficiales, no
  comprende el uso real.
- **El analizador estático es más preciso en su terreno.** Bandit y Ruff dan menos falsos positivos y
  son unas diez veces más rápidos; el modelo aporta cobertura (casos que las reglas no tienen) a
  cambio de ruido.
- **La inyección de prompts funciona en una dirección.** Con una orden para *fabricar* un hallazgo
  (caso `adv02`), los dos agentes informaron de un «secreto crítico» inexistente. La orden de *callar*
  un fallo real (caso `adv01`) no funcionó con este modelo.

## 8. Uso de IA y autoría

### 8.1 Qué hizo el asistente

Un asistente de IA (Claude Code) generó, a petición del autor: el código del revisor, los tests, los
workflows, la documentación, el arnés de evaluación y los casos de prueba. Ejecutó los tests y las
pruebas contra el servidor Ollama.

### 8.2 Decisiones del autor

Entre las alternativas que se le presentaron, el autor decidió:
- el **tema** (revisor de código con agentes, entre cinco ideas propuestas);
- el **framework** (LangChain/LangGraph, en lugar de Google ADK);
- el **modelo** (local con Ollama, en lugar de una API de pago);
- que el repositorio fuera **independiente** del código de la empresa;
- aportar el **servidor Ollama** y pedir la **revisión crítica** del trabajo y su corrección.

### 8.3 Errores del asistente y cómo se detectaron

| Error | Quién lo detectó | Corrección |
|---|---|---|
| Un helper llamado `tests_summary` lo recogía pytest como si fuera un test | La ejecución de pytest | Renombrado |
| La consola de Windows fallaba al imprimir emojis | Ejecutar contra el modelo real | Forzar UTF-8 |
| Toda la salida con gravedad baja, sin líneas y con hallazgos duplicados entre agentes | Primera prueba con el modelo real | Escalas de gravedad, líneas numeradas, deduplicación |
| El parser de diff desplazaba líneas ante `\ No newline…` o `++ ` (E1, E2) | Revisión externa | Parser basado en recuentos de hunk |
| El recorte podía dejar el prompt vacío (E3) | Revisión externa | Recorte repartido y aviso en el informe |
| La documentación afirmaba «no se ejecuta código del PR», y era falso (E4) | Revisión externa | `pull_request_target`, documentación corregida |
| Se atribuyó a las defensas la resistencia a una inyección que la versión anterior también resistía | Comprobación con el commit anterior | La conclusión se corrigió |
| La documentación decía que el modelo resistía la inyección de prompts | La evaluación (caso `adv02`) | Corregido en este documento y en `amenazas.md` |
| Se dio por hecho que el TFM exigía una memoria con estado del arte | Lectura del PDF oficial | Se reorientó a los requisitos reales |

Que varios errores los encontrara una revisión externa y no el desarrollo es información relevante
para el tribunal, y se declara aquí tal cual.

### 8.4 Cómo se verificó

74 tests automáticos y `ruff` en verde; ejecución real contra tres modelos; comparación con el commit
anterior para comprobar una conclusión; casos con resultado conocido para el arnés de evaluación.

### 8.5 Lo que debe completar el autor

> **[COMPLETAR]** Esta sección debe reflejar el trabajo y la comprensión **propios**. Un tribunal
> preguntará qué parte es tuya; conviene poder responder con ejemplos concretos:
>
> - Qué partes del código has leído y entiendes bien, y cuáles no. Prepárate para explicar sin
>   ayuda: cómo se reparte el trabajo entre los agentes en `graph.py`, por qué `parse_diff` usa los
>   recuentos de la cabecera `@@`, qué protege `escape_md` y por qué el workflow usa
>   `pull_request_target`.
> - Qué has cambiado tú, aunque sea poco, y por qué.
> - Dónde has discrepado del asistente.
> - Qué opinas de las etiquetas del conjunto de evaluación: cuáles discutirías.
> - Qué has aprendido y qué harías distinto.
>
> No debe rellenarlo nadie por ti: si no refleja lo que de verdad hiciste y entiendes, es lo primero
> que se nota en una defensa.

## 9. Seguridad

Modelo de amenazas completo en [amenazas.md](amenazas.md): revisor ejecutado desde la rama base,
permisos mínimos, sin PRs de forks, token efímero de Actions, salida del modelo escapada y modelo
local. La defensa frente a inyección de prompts es **parcial** y la evaluación confirma que no basta.

## 10. Limitaciones y trabajo futuro

**Limitaciones.** Falsos positivos frecuentes en un modelo de 7B; recorte de diffs grandes; contexto
limitado al diff; solo Python evaluado; evaluación pequeña y con etiquetas de un solo autor; no se ha
probado con PRs reales en GitHub Actions.

**Trabajo futuro**
- **Reducir los falsos positivos**, que es lo que más pesa. Ideas con coste bajo: exigir al modelo
  una cita literal de la línea que motiva el hallazgo y descartar los que no coincidan con el diff
  (esto bloquearía los hallazgos fabricados por inyección); un paso de verificación por un segundo
  agente; combinar con Bandit y Ruff y usar el modelo solo para lo que las reglas no cubren.
- Comentarios en línea sobre las líneas afectadas.
- Evaluar con PRs reales y con un conjunto etiquetado por más de una persona.
- Probar otros modelos y otros lenguajes.

## 11. Planificación

Trabajo realizado de forma intensiva en pocos días de noviembre de 2026, tras terminar el contenido
del máster.

| Fase | Contenido | Fechas |
|---|---|---|
| 1. Diseño y esqueleto | Elección de tema, framework y modelo; agentes, grafo y CLI | **[COMPLETAR]** |
| 2. Pruebas con el modelo real | Ajuste de prompts, gravedades, deduplicación | **[COMPLETAR]** |
| 3. Documentación | README, arquitectura, despliegue, pruebas | **[COMPLETAR]** |
| 4. Revisión crítica y correcciones | Errores E1–E4, diseño D1–D7, modelo de amenazas | **[COMPLETAR]** |
| 5. Evaluación | Casos, arnés, líneas base y tres modelos | **[COMPLETAR]** |
| 6. Entrega | Repositorio público, PRs de demostración, slides, vídeo y formulario | **[COMPLETAR]** |

## 12. Conclusiones

> **[COMPLETAR]** Redactar cuando estén los resultados finales. Debe responder, con cifras: ¿aporta
> el modelo algo frente a Bandit y Ruff?, ¿es utilizable con este nivel de falsos positivos?, ¿qué
> habría que cambiar? Las observaciones del apartado 7 ya apuntan a que, tal como está, sirve como
> ayuda a un revisor humano pero no como filtro automático.

## Bibliografía y enlaces

Consultar y anotar la fecha de acceso de cada uno **[COMPLETAR fechas]**:

- OWASP Top 10 — https://owasp.org/Top10/
- OWASP Top 10 for LLM Applications — https://genai.owasp.org/
- LangGraph — https://langchain-ai.github.io/langgraph/
- Ollama — https://ollama.com
- Bandit — https://bandit.readthedocs.io/
- Ruff — https://docs.astral.sh/ruff/
- uv — https://docs.astral.sh/uv/
- Seguridad en GitHub Actions (`pull_request_target`, runners propios) —
  https://docs.github.com/actions/security-for-github-actions
- PR-Agent — https://github.com/qodo-ai/pr-agent
- CodeRabbit — https://www.coderabbit.ai/
- Semgrep — https://semgrep.dev/ · SonarQube — https://www.sonarsource.com/products/sonarqube/

## Anexos

- Código: este repositorio.
- Workflows: `.github/workflows/`.
- Casos de evaluación: `eval/dataset/` y `src/revisor/evaluation/cases.py`.
- Resultados crudos: `eval/results/`.
