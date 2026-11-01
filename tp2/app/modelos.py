"""Modelos: estados, tarea interna y schema de entrada."""
from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Estado(str, Enum):
    PENDIENTE = "pendiente"
    EJECUTANDO = "ejecutando"
    COMPLETADA = "completada"
    FALLIDA = "fallida"
    CANCELADA = "cancelada"


TERMINALES = frozenset({Estado.COMPLETADA, Estado.FALLIDA, Estado.CANCELADA})


class NuevaTarea(BaseModel):
    tipo: Literal["descargar", "hashear", "esperar"]
    parametros: dict[str, Any]
    timeout: float | None = Field(default=None, gt=0)


@dataclass
class Tarea:
    tipo: str
    parametros: dict
    timeout: float
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    estado: Estado = Estado.PENDIENTE
    resultado: Any = None
    error: str | None = None
    creada: float = field(default_factory=time.time)
    iniciada: float | None = None
    terminada: float | None = None
    # asyncio.Task que corre la tarea; no se serializa.
    _task: asyncio.Task | None = field(default=None, repr=False, compare=False)

    def a_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "parametros": self.parametros,
            "timeout": self.timeout,
            "estado": self.estado.value,
            "resultado": self.resultado,
            "error": self.error,
            "creada": self.creada,
            "iniciada": self.iniciada,
            "terminada": self.terminada,
        }
