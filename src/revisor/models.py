from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high"]


class LLMFinding(BaseModel):
    """Hallazgo tal y como lo devuelve el modelo (salida estructurada)."""

    file: str = Field(description="Ruta del fichero tal y como aparece en el diff")
    line: int | None = Field(default=None, description="Línea nueva afectada, si se conoce")
    severity: Severity = "low"
    title: str = Field(description="Resumen corto del problema")
    evidence: str = Field(
        default="",
        description=(
            "Cita LITERAL, copiada sin cambios, del fragmento de la línea añadida que motiva el "
            "problema (sin el prefijo L<n>: ni el signo +). Si no puedes citar una línea real del "
            "diff, no reportes el problema."
        ),
    )
    detail: str = Field(description="Por qué es un problema en este cambio")
    suggestion: str = Field(default="", description="Cómo corregirlo")


class LLMFindings(BaseModel):
    findings: list[LLMFinding] = Field(default_factory=list)


class Finding(LLMFinding):
    """Hallazgo ya atribuido a un agente."""

    agent: str
