# Resultados de la evaluación

_Generado por `revisor.evaluation.run report`._

Casos: **29** · etiquetas esperadas: **21**

## Resumen (línea exacta)

| Sistema | Agente | TP | FP | FN | Precisión | Exhaustividad | F1 |
|---|---|---|---|---|---|---|---|
| qwen2.5:7b-instruct | security | 10 | 12 | 1 | 0.45 | 0.91 | 0.61 |
| qwen2.5:7b-instruct | smells | 5 | 20 | 1 | 0.20 | 0.83 | 0.32 |
| qwen2.5:7b-instruct | tests | 2 | 5 | 2 | 0.29 | 0.50 | 0.36 |
| qwen2.5:7b-instruct | **informe final** | 17 | 37 | 4 | 0.31 | 0.81 | 0.45 |
| qwen3:8b | security | 3 | 21 | 8 | 0.12 | 0.27 | 0.17 |
| qwen3:8b | smells | 2 | 38 | 4 | 0.05 | 0.33 | 0.09 |
| qwen3:8b | tests | 1 | 12 | 3 | 0.08 | 0.25 | 0.12 |
| qwen3:8b | **informe final** | 11 | 66 | 10 | 0.14 | 0.52 | 0.22 |
| bandit | security | 7 | 5 | 4 | 0.58 | 0.64 | 0.61 |
| ruff | smells | 4 | 3 | 2 | 0.57 | 0.67 | 0.62 |

«Línea exacta»: el hallazgo debe caer en la línea etiquetada (±1).

## Solo el fichero (se perdona la línea)

| Sistema | Agente | TP | FP | FN | Precisión | Exhaustividad | F1 |
|---|---|---|---|---|---|---|---|
| qwen2.5:7b-instruct | security | 10 | 12 | 1 | 0.45 | 0.91 | 0.61 |
| qwen2.5:7b-instruct | smells | 6 | 19 | 0 | 0.24 | 1.00 | 0.39 |
| qwen2.5:7b-instruct | tests | 3 | 4 | 1 | 0.43 | 0.75 | 0.55 |
| qwen3:8b | security | 10 | 14 | 1 | 0.42 | 0.91 | 0.57 |
| qwen3:8b | smells | 5 | 35 | 1 | 0.12 | 0.83 | 0.22 |
| qwen3:8b | tests | 4 | 9 | 0 | 0.31 | 1.00 | 0.47 |
| bandit | security | 7 | 5 | 4 | 0.58 | 0.64 | 0.61 |
| ruff | smells | 4 | 3 | 2 | 0.57 | 0.67 | 0.62 |

## Falsos positivos en casos sin problemas y tiempo

| Sistema | Casos sin problemas con falso positivo | Tiempo por caso | Agentes caídos |
|---|---|---|---|
| qwen2.5:7b-instruct | 6 de 9 | 7.9 s (mediana 8.5, p95 17.6) | 0 |
| qwen3:8b | 7 de 9 | 807.3 s (mediana 226.1, p95 3100.5) | 0 |
| bandit | 1 de 9 | 0.9 s (mediana 0.9, p95 1.3) | 0 |
| ruff | 0 de 9 | 0.3 s (mediana 0.3, p95 0.5) | 0 |

## Por tipo de caso (informe final, línea exacta)

| Sistema | Categoría | Casos | TP | FP | FN |
|---|---|---|---|---|---|
| qwen2.5:7b-instruct | security | 10 | 9 | 10 | 1 |
| qwen2.5:7b-instruct | smells | 6 | 5 | 6 | 1 |
| qwen2.5:7b-instruct | tests | 3 | 2 | 3 | 2 |
| qwen2.5:7b-instruct | clean | 8 | 0 | 14 | 0 |
| qwen2.5:7b-instruct | adversarial | 2 | 1 | 4 | 0 |
| qwen3:8b | security | 10 | 4 | 23 | 6 |
| qwen3:8b | smells | 6 | 3 | 12 | 3 |
| qwen3:8b | tests | 3 | 3 | 11 | 1 |
| qwen3:8b | clean | 8 | 0 | 17 | 0 |
| qwen3:8b | adversarial | 2 | 1 | 3 | 0 |

