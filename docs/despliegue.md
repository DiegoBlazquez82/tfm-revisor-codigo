# Despliegue e integración con GitHub Actions

## Requisitos

- Un repositorio en GitHub con este código.
- Un servidor Ollama accesible desde el runner, con un modelo que soporte salida estructurada.
  Probado con `qwen2.5:7b-instruct`.
- Un **runner propio** (self-hosted) con la etiqueta `ollama`, dentro de la red desde la que se ve
  el servidor Ollama. Los runners de GitHub no alcanzan direcciones internas.

## Pasos

### 1. Preparar Ollama

```bash
ollama pull qwen2.5:7b-instruct
curl http://<servidor>:11434/api/tags      # debe listar el modelo
```

### 2. Registrar el runner

En GitHub: *Settings → Actions → Runners → New self-hosted runner*. Sigue las instrucciones y,
al configurarlo, añade la etiqueta `ollama`. Instala [uv](https://docs.astral.sh/uv/) en esa
máquina (el workflow ejecuta `astral-sh/setup-uv`, pero conviene tenerlo disponible).

### 3. Configurar la URL de Ollama

*Settings → Secrets and variables → Actions → Variables*:

| Variable | Valor de ejemplo |
|---|---|
| `OLLAMA_BASE_URL` | `http://10.1.10.21:11434` |

Es una **variable**, no un secreto: no es una credencial. Si no existe, el workflow usa
`http://localhost:11434`.

No hace falta crear ningún token: el workflow usa `secrets.GITHUB_TOKEN`, que GitHub genera en cada
ejecución, con los permisos que declara el propio workflow.

### 4. Probarlo

Abre un PR que modifique código. En la pestaña *Actions* aparece «Revisión del PR con agentes» y,
al terminar, un comentario con el informe en el PR. Un nuevo push actualiza ese mismo comentario.

## Workflows

| Fichero | Cuándo corre | Qué hace |
|---|---|---|
| `ci.yml` | push a `main` y cualquier PR | `ruff` y `pytest` en un runner de GitHub |
| `pr-review.yml` | PR abierto, actualizado o reabierto | Ejecuta el revisor y comenta en el PR |

## Seguridad del despliegue

- **Permisos mínimos:** `contents: read` y `pull-requests: write`.
- **Sin PRs de forks:** el job se salta si el PR viene de otro repositorio. Ahí `GITHUB_TOKEN` no
  puede comentar y, sobre todo, no se debe ejecutar código no confiable en un runner propio.
- **No se ejecuta código del PR.** El revisor solo lee el diff como texto a través de la API.
- **Concurrencia:** un push nuevo cancela la revisión anterior del mismo PR.
- **Tiempo máximo:** 15 minutos por ejecución.
- **Datos:** el contenido del diff se envía al servidor Ollama indicado. Al ser un servidor propio,
  el código no sale de la red; si usaras un proveedor externo, habría que valorarlo.

## Probar sin GitHub

```bash
uv run revisor review --diff-file examples/vulnerable.diff
```

con `OLLAMA_BASE_URL` y `OLLAMA_MODEL` en el entorno si no usas los valores por defecto.

## Problemas frecuentes

| Síntoma | Causa probable |
|---|---|
| El job se queda en «Waiting for a runner» | Ningún runner con la etiqueta `ollama` está conectado |
| `ConnectError` al llamar al modelo | El runner no ve `OLLAMA_BASE_URL` (red o firewall) |
| `model not found` | El modelo de `OLLAMA_MODEL` no está descargado en el servidor |
| No aparece el comentario | Falta el permiso `pull-requests: write` o el PR es de un fork |
| Salen caracteres raros en la consola de Windows | Usa la versión actual: fuerza UTF-8 al imprimir |
