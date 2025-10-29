"""
Pydantic schema for ADK Scorer output
Defines the structured JSON response format for news scoring
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class Severity(str, Enum):
    """Severity levels for mobility news"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ScoringResponse(BaseModel):
    """
    Structured output schema for mobility news scoring

    This schema is enforced by Google ADK's output_schema parameter,
    ensuring all responses are validated and properly formatted.
    """

    keep: bool = Field(
        description="Si la noticia es relevante para el sistema de alertas de movilidad"
    )

    severity: Optional[Severity] = Field(
        description="Nivel de severidad del impacto en movilidad (solo si keep=true)",
        default=None
    )

    tags: List[str] = Field(
        description="Lista de etiquetas relevantes (transporte, tipo, impacto, temporal)",
        min_length=1
    )

    area: str = Field(
        description="Área geográfica o línea de transporte afectada"
    )

    entities: List[str] = Field(
        description="Entidades mencionadas (instituciones, lugares, estaciones)",
        default_factory=list
    )

    summary: str = Field(
        description="Resumen conciso de 1-2 frases del impacto en movilidad",
        min_length=10
    )

    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Score de relevancia entre 0.0 (no relevante) y 1.0 (muy relevante)"
    )

    reasoning: str = Field(
        description="Justificación breve de la decisión de clasificación",
        min_length=10
    )

    class Config:
        """Pydantic configuration"""
        json_schema_extra = {
            "example": {
                "keep": True,
                "severity": "high",
                "tags": ["metro", "suspension", "urgente"],
                "area": "Linea_A_Metro",
                "entities": ["Metro de Medellín", "Estación Niquía"],
                "summary": "Suspensión temporal de Línea A del Metro por mantenimiento entre Niquía y Bello.",
                "relevance_score": 0.95,
                "reasoning": "Afecta directamente el servicio principal de transporte masivo de la ciudad"
            }
        }
