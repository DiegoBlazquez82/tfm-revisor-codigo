# Requisitos del TFM y dónde se cumplen

Fuente: *Documentación complementaria TFM — Módulo 12: Proyecto Final* (PDF oficial del máster,
`MDEV3_Documentacion-TFM-Fundae.docx.pdf`), leído el 3 nov 2026.

> **Importante.** El PDF **no pide una memoria académica** (estado del arte, bibliografía…). Pide un
> README con apartados concretos, el código en un repositorio público, un despliegue, unas slides y un
> vídeo, entregados mediante un formulario. La memoria de este repositorio (`docs/memoria-tfm.md`)
> es un extra, no un requisito.

## Objetivo que fija el máster

Una aplicación real, original y adaptada al nivel del alumno, que demuestre lo aprendido. El tipo de
software es libre. Esto encaja con el proyecto: una herramienta de revisión de código con agentes
que usa LangGraph, un modelo local, seguridad, CI/CD y pruebas.

## Entregables

| # | Requisito del PDF | Dónde está | Estado |
|---|---|---|---|
| 1a | README: descripción general | `README.md` §1 | Hecho |
| 1b | README: stack tecnológico | `README.md` §2 | Hecho |
| 1c | README: instalación y ejecución | `README.md` §3 | Hecho (probado en local con `uv`) |
| 1d | README: estructura del proyecto | `README.md` §4 | Hecho |
| 1e | README: funcionalidades principales | `README.md` §5 | Hecho |
| 1f | README: usuario y contraseña de prueba (si hay login) | `README.md` §6 | Hecho: no aplica, no hay login |
| 2 | Código fuente en **repositorio público** de GitHub (o privado justificado, con permisos para el email que indica el PDF) | Carpeta local, sin remoto | **Pendiente** |
| 3 | Despliegue o publicación (recomendado) con URL, añadida también a la documentación | Ver «Despliegue» abajo | **Pendiente** |
| 4 | Slides con URL pública o documento adjunto en el repositorio | — | **Pendiente** |
| 5 | Vídeo con explicación y **captura de pantalla obligatoria**; URL pública | — | **Pendiente** |
| — | La documentación, la información de despliegue y las slides deben estar también en el directorio del código | `docs/`, `README.md`; faltan las slides | Parcial |
| — | Formulario de entrega (nombre, email de inscripción, URLs, usuario de prueba) | Lección «Proyecto Final» del campus | **Pendiente (lo envía el autor)** |

## Fecha de entrega: hay una contradicción que aclarar

- El PDF dice que la fecha de entrega **es la reflejada en el temario (26/10/2026)**. A 3 nov 2026
  **ya ha pasado**.
- La lección «Proyecto Final» del campus dice que, para bonificar con FUNDAE, el TFM debe estar
  entregado **antes del 30/11/2026** (no hace falta que esté corregido).

Son dos fechas distintas y pueden convivir (una de calificación y otra de bonificación), pero no está
claro. **Conviene preguntar al tutor por escrito** si se admite la entrega ahora y con qué
consecuencias, antes de preparar el resto.

## Despliegue: qué significa para este proyecto

Esta herramienta no es una web con URL. Lo que puede ofrecerse como «proyecto en funcionamiento» es:

- el **repositorio público** con el workflow `pr-review.yml`, y
- **uno o varios PRs de demostración** en ese repositorio, con el comentario que publica el revisor.
  La URL de uno de esos PRs sirve de enlace de despliegue.

### Advertencia de seguridad: repositorio público + runner propio

GitHub desaconseja usar runners propios en repositorios **públicos**: cualquiera puede abrir un PR e
intentar ejecutar código en esa máquina. Este proyecto lo mitiga (`pull_request_target`, revisor
desde la rama base, sin PRs de forks, permisos mínimos; ver [amenazas.md](amenazas.md)), pero no
elimina el riesgo. Opciones para la demostración, de más a menos segura:

1. **Generar los PRs de demostración tú mismo** y ejecutar el revisor a mano
   (`revisor review --repo … --pr … --post`) desde tu equipo, sin registrar ningún runner en el
   repositorio público. Es suficiente para mostrar el comentario en el PR.
2. Registrar el runner solo mientras se hacen las pruebas y eliminarlo después.
3. Mantener el runner activo de forma permanente: no recomendado en un repositorio público.

## Checklist de entrega

- [ ] Preguntar al tutor por la fecha (26/10 frente a 30/11).
- [ ] Publicar el repositorio en GitHub (público) y comprobar que no hay secretos ni datos de la empresa.
- [ ] Abrir PRs de demostración y copiar la URL de uno al README (enlace de despliegue).
- [ ] Grabar el vídeo (captura de pantalla obligatoria) y subirlo; copiar la URL al README.
- [ ] Preparar las slides, subirlas y copiar la URL al README (o adjuntarlas en `docs/`).
- [ ] Rellenar el formulario de la lección «Proyecto Final».
