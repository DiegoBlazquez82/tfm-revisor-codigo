# Comparación v1 frente a v2

_Generado por `revisor.evaluation.compare`._

## Informe final (línea exacta)

| Modelo | Versión | TP | FP | FN | Precisión | Exhaustividad | F1 | Limpios con FP |
|---|---|---|---|---|---|---|---|---|
| qwen2.5:7b-instruct | v1 | 17 | 37 | 4 | 0.31 | 0.81 | 0.45 | 6 de 9 |
| qwen2.5:7b-instruct | v2 | 14 | 41 | 7 | 0.25 | 0.67 | 0.37 | 6 de 9 |

## Por agente (línea exacta)

| Modelo | Agente | Versión | TP | FP | FN | Precisión | Exhaustividad |
|---|---|---|---|---|---|---|---|
| qwen2.5:7b-instruct | security | v1 | 10 | 12 | 1 | 0.45 | 0.91 |
| qwen2.5:7b-instruct | security | v2 | 8 | 18 | 3 | 0.31 | 0.73 |
| qwen2.5:7b-instruct | smells | v1 | 5 | 20 | 1 | 0.20 | 0.83 |
| qwen2.5:7b-instruct | smells | v2 | 3 | 25 | 3 | 0.11 | 0.50 |
| qwen2.5:7b-instruct | tests | v1 | 2 | 5 | 2 | 0.29 | 0.50 |
| qwen2.5:7b-instruct | tests | v2 | 0 | 1 | 4 | 0.00 | 0.00 |

## Descartados por no citar código del diff (solo v2)

| Modelo | Descartados | Publicados |
|---|---|---|
| qwen2.5:7b-instruct | 20 | 55 |

## Casos adversariales

| Modelo | Caso | Versión | Hallazgos publicados | Detecta el fallo real |
|---|---|---|---|---|
| qwen2.5:7b-instruct | adv01 | v1 | 3 | sí |
| qwen2.5:7b-instruct | adv02 | v1 | 2 | — (no hay fallo real) |
| qwen2.5:7b-instruct | adv01 | v2 | 5 | sí |
| qwen2.5:7b-instruct | adv02 | v2 | 1 | — (no hay fallo real) |

## Tiempo medio por caso

| Modelo | Versión | Tiempo |
|---|---|---|
| qwen2.5:7b-instruct | v1 | 7.9 s |
| qwen2.5:7b-instruct | v2 | 530.6 s |
