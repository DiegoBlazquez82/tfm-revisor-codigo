# Guion del vídeo y datos para el formulario de entrega

El vídeo **debe grabarse con captura de pantalla** (lo exige el PDF del máster, ver
[requisitos-tfm.md](requisitos-tfm.md)). Duración orientativa: 6–7 minutos. Las slides están en
[presentacion.pptx](presentacion.pptx); el texto de cada una está en sus notas del orador.

## Antes de grabar

1. Tener abierto un PR de demostración con el comentario del revisor ya publicado (ver
   [despliegue.md](despliegue.md)).
2. Tener el repositorio abierto en el navegador y una terminal en la carpeta del proyecto.
3. Probar antes `uv run revisor review --diff-file examples/vulnerable.diff` con el Ollama accesible.

## Guion

| Min | Qué se ve | Qué se dice |
|---|---|---|
| 0:00 | Slide 1 | Qué es el proyecto y que está evaluado con datos, también lo que no salió bien |
| 0:30 | Slides 2–3 | Problema y arquitectura: tres agentes en paralelo y un agregador |
| 1:30 | Slide 4 | Seguridad: `pull_request_target`, diff como dato, salida escapada. Contar el error corregido |
| 2:30 | Terminal | Ejecutar `uv run pytest` (tests sin modelo) y `uv run revisor review --diff-file examples/vulnerable.diff` |
| 3:30 | Navegador | Abrir el PR de demostración y mostrar el comentario único; hacer un push y ver que se actualiza |
| 4:30 | Slides 5–6 | Metodología y resultados frente a Bandit y Ruff |
| 5:30 | Slide 7 | La mejora de la cita literal que no funcionó |
| 6:15 | Slide 8 | Conclusiones y límites |

## Datos para el formulario de la lección «Proyecto Final»

Rellenar a mano; no se ha enviado nada en nombre del autor.

| Campo | Valor |
|---|---|
| Repositorio público | https://github.com/DiegoBlazquez82/tfm-revisor-codigo |
| Despliegue / acceso | https://github.com/DiegoBlazquez82/tfm-revisor-codigo/pull/1 |
| Slides | https://github.com/DiegoBlazquez82/tfm-revisor-codigo/blob/main/docs/presentacion.pptx |
| Vídeo | URL del vídeo **(pendiente)** |
| Usuario y contraseña de prueba | No aplica: no hay login |

Antes de enviar: comprobar que el README tiene todos los enlaces y que la fecha límite es la correcta
(26/10 en el PDF frente a 30/11 en la lección).
