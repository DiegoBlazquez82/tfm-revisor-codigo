# Guion del vídeo: texto para leer (6–7 minutos)

Las indicaciones **[ENTRE CORCHETES]** son acciones en pantalla, no se leen. El minutado y la
preparación están en [guion-video-y-entrega.md](guion-video-y-entrega.md). Léelo con tus palabras: es
mejor que suene a ti y no a texto leído.

## 0:00 · Presentación (slide 1)

Hola, soy Diego Blázquez y esta es la presentación de mi trabajo final del Máster en Desarrollo con
IA: un revisor de código con agentes. Es un sistema que revisa un pull request y publica un único
comentario con problemas de seguridad, de calidad y de pruebas, usando un modelo de lenguaje local.
Voy a enseñar cómo funciona, cómo lo he evaluado y, sobre todo, qué resultados salieron bien y cuáles
no.

## 0:30 · Problema y solución (slides 2 y 3)

La revisión de código es un cuello de botella, y los revisores humanos pasan por alto cosas
repetitivas: secretos escritos en el código, inyecciones SQL, falta de tests. Además, en muchos
equipos el código no puede enviarse a un servicio externo. Por eso uso un modelo local con Ollama.

El diff del pull request entra en un grafo de LangGraph. Tres agentes trabajan en paralelo: seguridad,
con criterios de OWASP, calidad de código y pruebas. Un agregador junta los resultados, elimina
duplicados, los ordena por gravedad y publica un único comentario, que se actualiza en cada push. Si un
agente falla, el informe lo dice; nunca afirma que todo está bien si algo falló.

## 1:30 · Seguridad (slide 4)

Un revisor lee texto de terceros y publica en un sitio visible, así que es un objetivo. Las medidas son
cuatro. Primera, en GitHub Actions uso `pull_request_target`: el workflow y el revisor salen de la
rama base y el contenido del PR solo se lee como texto. Segunda, el diff va delimitado como dato y no
puede cerrar su delimitador. Tercera, todo lo que escribe el modelo se escapa antes de publicarse.
Cuarta, el revisor solo reconoce como suyo el comentario del bot de GitHub Actions.

Quiero contar un error mío: una versión anterior de la documentación decía que no se ejecutaba código
del pull request, y era falso. Lo detectó la revisión de mi trabajo y lo corregí.

## 2:30 · Demostración en terminal

[ABRE LA TERMINAL EN LA CARPETA DEL PROYECTO]

Primero ejecuto los tests. No necesitan el modelo, porque usan uno simulado.

[EJECUTA: `uv run pytest`]

Son 89 tests y pasan. La revisión con el modelo real la enseño con el resultado ya guardado, porque el
servidor de Ollama que uso corre ahora sin GPU y cada revisión tarda minutos; no tiene sentido
esperarla en directo. Ese resultado es el comentario de este pull request.

## 3:30 · Pull request de demostración

[ABRE https://github.com/DiegoBlazquez82/tfm-revisor-codigo/pull/1]

Este es un pull request de demostración con tres fallos deliberados. Aquí está el comentario del
revisor con cuatro hallazgos. Debo ser claro: no lo ha publicado el workflow automático, porque mi
servidor de Ollama está en una red interna y el repositorio es público, y por seguridad no he dejado
un runner permanente. Generé el comentario ejecutando el revisor en mi máquina y lo publiqué a mano. El
workflow está en el repositorio y se activaría con un runner propio.

[OPCIONAL: ENSEÑA `.github/workflows/pr-review.yml`]

## 4:30 · Evaluación (slides 5 y 6)

Para no quedarme en «parece que funciona», construí 29 casos con 21 hallazgos etiquetados y 9 casos
sin problemas. Un hallazgo cuenta como acierto si cae en la línea etiquetada. Lo comparé con Bandit y
Ruff y probé dos modelos.

Con qwen2.5 el informe final tiene una exhaustividad de 0,81 pero una precisión de 0,31: encuentra casi
todo, pero dos de cada tres hallazgos son falsos, y en seis de nueve casos correctos puso algún aviso.
Bandit y Ruff tienen una precisión de 0,58 y 0,57. El modelo aporta cobertura, por ejemplo tests sin
aserciones, y las reglas aportan precisión. Un modelo mayor no fue mejor: qwen3 de 8 mil millones salió
peor, con un F1 de 0,22, y qwen3.5 falló al devolver el formato.

## 5:30 · Una mejora que no funcionó (slide 7)

Esperaba que exigir al modelo una cita literal de la línea, y descartar lo que no apareciera en el
diff, redujera los falsos positivos y los hallazgos inventados. Con los mismos casos empeoró: el F1 bajó
de 0,45 a 0,37. Descartó veinte hallazgos, pero también aciertos mal citados, y no detecta errores de
fondo. Lo cuento porque es parte del resultado.

## 6:15 · Conclusiones (slide 8)

Mi conclusión es que sirve como ayuda a un revisor humano, no como filtro automático. Aporta cobertura
que las reglas no tienen, pero con más ruido, y las defensas por prompt no bastan contra hallazgos
inventados. Los límites: casos sintéticos, una ejecución por modelo y tiempos con el servidor
compartido. El siguiente paso sería combinar reglas y modelo, y repetir las ejecuciones. Todo el código,
la documentación y los resultados están en el repositorio. Gracias.
