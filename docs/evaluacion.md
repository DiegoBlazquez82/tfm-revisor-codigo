# Evaluación experimental

Cubre el punto B1 de la revisión del tribunal: medir de verdad qué detecta el revisor, cuánto se
equivoca, frente a qué se compara y cuánto tarda. Los números están en
[evaluacion-resultados.md](evaluacion-resultados.md) (generado por el propio arnés).

## Preguntas

1. **¿Encuentra los problemas?** Exhaustividad por agente.
2. **¿Se inventa problemas?** Precisión y falsos positivos, sobre todo en código correcto.
3. **¿Aporta algo frente a un analizador estático gratuito?** Comparación con Bandit y Ruff.
4. **¿Qué modelo conviene?** Tres modelos disponibles en el servidor Ollama.
5. **¿Cuánto tarda una revisión?** Tiempo por caso.
6. **¿Resiste a una orden escondida en el código?** Casos adversariales.

## Conjunto de casos

29 casos en `src/revisor/evaluation/cases.py`, exportados como diffs en `eval/dataset/`.

| Tipo | Casos | Qué contiene |
|---|---|---|
| Seguridad | 10 | Inyección SQL, secreto en el código, inyección de comandos, deserialización insegura, hash débil, path traversal, SSRF, XSS, falta de autorización, TLS desactivado |
| Calidad | 6 | Anidamiento, función larga, números mágicos, código duplicado, `except` que traga errores, código muerto |
| Tests | 3 | Tests sin aserciones, test que llama a la red real, aserción sin sentido |
| Limpios | 8 | Código correcto, varios que **parecen** peligrosos (SQL parametrizado, `subprocess` seguro, hash con `scrypt`, ruta confinada) |
| Adversariales | 2 | Una orden escondida que pide callar un fallo real, y otra que pide inventar un hallazgo |

Total: **21 etiquetas** de problemas esperados.

### Cómo se etiquetan

Cada línea problemática lleva una marca `#@ agente:tipo` en el código fuente del caso. Antes de
enseñar el código al revisor, las marcas se retiran y se genera un diff de «fichero nuevo». Las líneas
esperadas se calculan a partir de las marcas, así que **no se pueden desfasar** al editar un caso.
Hay tests que comprueban que cada etiqueta cae en una línea realmente añadida y que ninguna marca
llega al modelo.

## Métricas

Un hallazgo del revisor es un **acierto (TP)** si coincide con una etiqueta; **falso positivo (FP)**
si no coincide con ninguna; y una etiqueta sin hallazgo es una **omisión (FN)**. Cada etiqueta se
empareja como mucho con un hallazgo.

- **Línea exacta:** mismo fichero y línea dentro del rango etiquetado, con ±1 de tolerancia.
- **Solo fichero:** basta con acertar el fichero (perdona que el modelo se equivoque de línea).
- **Por agente:** cada agente se puntúa solo contra las etiquetas de su materia. Que el agente de
  calidad opine sobre seguridad cuenta como falso positivo suyo.
- **Informe final:** lo que se publicaría, sin importar qué agente lo dijo.
- **Casos limpios:** cuántos casos sin problemas reciben al menos un hallazgo.
- El aviso «código modificado sin tests» lo da una **regla**, no el modelo, y se excluye de la
  puntuación del modelo (se prueba aparte con tests unitarios).

Precisión = TP/(TP+FP); exhaustividad = TP/(TP+FN); F1 es su media armónica.

## Líneas base (sin IA)

- **Bandit** para seguridad (se desactiva B101, el `assert` de los tests).
- **Ruff** para calidad, con reglas de complejidad (C901 con umbral 4), nº de parámetros, valores
  mágicos, `except` desnudo y exceso de anidamiento.
- **Semgrep no se incluye:** no tiene soporte oficial en Windows, donde se ha desarrollado.

## Modelos

Se usan los tres del servidor Ollama, con temperatura 0 y la misma entrada:

| Modelo | Parámetros | Cuantización |
|---|---|---|
| `qwen2.5:7b-instruct` | 7,6 B | Q4_K_M |
| `qwen3:8b` | 8,2 B | Q4_K_M |
| `qwen3.5:9b` | 9,7 B | Q4_K_M |

## Limitaciones (importantes)

Estas limitaciones condicionan lo que se puede afirmar con los resultados:

1. **Casos sintéticos y pequeños.** 29 casos con 21 etiquetas dan intervalos de confianza muy
   anchos. Una diferencia de uno o dos aciertos entre modelos **no es significativa**.
2. **Un solo etiquetador, y no humano.** Las etiquetas las escribió un asistente de IA al crear los
   casos; no las ha validado una segunda persona. Cada caso se diseñó para tener un problema claro,
   así que son más fáciles que el código real. **Conviene que el autor del TFM las revise** y deje
   constancia de cuáles discute.
3. **Solo Python y solo ficheros nuevos.** El revisor admite modificaciones de ficheros existentes,
   pero aquí no se mide.
4. **No se mide la utilidad real.** Que un hallazgo coincida con una etiqueta no dice si ayudaría a un
   revisor humano en un PR de verdad. Eso solo lo da la prueba en GitHub (punto B5).
5. **Los modelos no son del todo deterministas** aunque la temperatura sea 0; una repetición puede
   variar ligeramente. Se ha hecho una ejecución por modelo.
6. **El conjunto se escribió conociendo el revisor.** Hay riesgo de que los casos reflejen lo que se
   esperaba que detectara. Un conjunto externo (PRs reales con vulnerabilidades conocidas) sería más
   convincente.

## Cómo reproducirlo

```bash
uv sync --group eval
export OLLAMA_BASE_URL=http://<servidor>:11434

uv run python -m revisor.evaluation.run export-dataset          # diffs y etiquetas
uv run --group eval python -m revisor.evaluation.run baselines   # Bandit y Ruff
uv run python -m revisor.evaluation.run models --model qwen2.5:7b-instruct
uv run python -m revisor.evaluation.run report                   # genera docs/evaluacion-resultados.md
```

Los resultados crudos de cada ejecución quedan en `eval/results/*.json`, de modo que se puede
cambiar la puntuación y regenerar el informe sin volver a llamar al modelo.
