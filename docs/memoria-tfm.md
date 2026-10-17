# Memoria del TFM — borrador

> **Cómo usar este borrador.** Está escrito solo con hechos verificados en el repositorio. Las
> partes marcadas **[COMPLETAR]** dependen de ti (decisiones, experiencia, resultados que aún no
> existen). Antes de entregar, contrasta cada punto con el PDF de requisitos y criterios de
> evaluación del TFM, que no se ha leído al preparar este documento.

## 1. Título y resumen

**Revisor de código con agentes: seguridad, calidad y pruebas en pull requests.**

Sistema que, al abrirse un pull request, analiza su diff con tres agentes de IA especializados
(seguridad según OWASP Top 10, code smells y cobertura de pruebas), unifica los resultados y los
publica como un único comentario en el propio PR. Se ejecuta en GitHub Actions con un modelo de
lenguaje local servido por Ollama, de modo que el código no sale de la red de la organización.

## 2. Problema y objetivos

**Problema.** La revisión de código es un cuello de botella y los revisores humanos pasan por alto
cuestiones repetitivas (secretos escritos en el código, inyecciones, falta de tests).

**Objetivo general.** Ofrecer una primera revisión automática, rápida y consistente que ayude al
revisor humano.

**Objetivos específicos**
1. Detectar problemas de seguridad del OWASP Top 10 en el código añadido.
2. Señalar code smells que perjudican el mantenimiento.
3. Avisar cuando un cambio de código no trae pruebas.
4. Integrarlo en el flujo de trabajo (GitHub Actions) sin ejecutar código del PR.
5. Mantener el código dentro de la red mediante un modelo local.

**Fuera de alcance:** corregir el código automáticamente, sustituir la revisión humana, analizar
el repositorio completo.

## 3. Relación con los contenidos del máster

| Parte del proyecto | Módulos del máster |
|---|---|
| Grafo de agentes en paralelo con LangGraph | LangChain con Python, Multi-agents |
| Salida estructurada validada con Pydantic | LangChain con Python, Prompt engineering para developers |
| Modelo local con Ollama | Modelos de IA locales |
| Revisión OWASP, secretos, permisos mínimos | Seguridad (OWASP Top 10, desarrollo seguro) |
| Workflows de CI y de revisión | DevOps y CI/CD, Copilot dentro de GitHub |
| Tests automáticos con modelo simulado | Testing |
| Code smells como criterio de revisión | Code smells, refactor y deuda; Métricas |
| Documentación del proyecto | Documentación con IA |

## 4. Diseño

Ver [arquitectura.md](arquitectura.md). Resumen: tres agentes en paralelo (`security`, `smells`,
`tests`) con un prompt por criterio, un agregador que deduplica y ordena, y un cliente de GitHub
que crea o actualiza un único comentario.

Decisiones destacables:
- Un criterio por agente, con la indicación explícita de qué *no* revisar.
- La salida del modelo se trata como no fiable: se valida, se filtra y se deduplica.
- Lo que puede decidirse con reglas (código sin tests) no se delega en el modelo.

## 5. Implementación

Python 3.11, LangGraph, `langchain-ollama`, Pydantic y httpx; gestión con `uv`. Estructura y
responsabilidades de cada módulo en [arquitectura.md](arquitectura.md).

## 6. Pruebas y resultados

Ver [pruebas.md](pruebas.md).

- 15 tests automáticos, sin red ni modelo.
- Prueba con `qwen2.5:7b-instruct` sobre un diff inventado: se detectaron los tres problemas
  sembrados (secreto, inyección SQL, función con anidamiento excesivo) y la falta de tests.
- La primera ejecución mostró defectos (gravedad uniforme, sin líneas, duplicados entre agentes)
  que motivaron cambios concretos de diseño.

**[COMPLETAR]** Resultados sobre PRs reales una vez ejecutado en GitHub Actions: número de PRs,
hallazgos útiles, falsos positivos, tiempo medio por revisión.

## 7. Seguridad y privacidad

Ver [despliegue.md](despliegue.md). Permisos mínimos, sin ejecución de código del PR, sin PRs de
forks, token efímero de Actions, modelo local para que el código no salga de la red.

## 8. Uso de IA en el desarrollo

> Es una sección que se evalúa y debe reflejar **tu** trabajo real. Lo siguiente es lo que consta;
> ajústalo a la verdad.

**Hechos:**
- La implementación inicial, los tests y la documentación se generaron con un asistente de IA
  (Claude Code), a partir de decisiones tomadas por ti: tema, framework (LangChain/LangGraph),
  modelo local (Ollama) y ubicación del repositorio.
- El asistente ejecutó los tests y probó el revisor contra el servidor Ollama; los resultados
  están en [pruebas.md](pruebas.md).
- Durante el desarrollo el asistente corrigió fallos que él mismo había introducido (por ejemplo,
  un test mal nombrado que pytest recogía como test, y avisos de lint).

**[COMPLETAR]**
- Qué revisaste tú del código generado y cómo (lectura, ejecución, cambios que hiciste).
- Qué decidiste distinto de lo que propuso el asistente.
- Qué aprendiste y qué harías de otra forma.

## 9. Limitaciones y trabajo futuro

Limitaciones: recorte de diffs grandes, falsos positivos de un modelo pequeño, contexto limitado al
diff. Trabajo futuro posible: comentarios en línea sobre las líneas afectadas, comparación de
modelos, medición con un conjunto de PRs etiquetados, contexto del repositorio mediante RAG.

## 10. Conclusiones

**[COMPLETAR]** Cuando tengas resultados reales.

## Anexos

- Código: este repositorio.
- Workflows: `.github/workflows/`.
- Diff de ejemplo: `examples/vulnerable.diff`.
