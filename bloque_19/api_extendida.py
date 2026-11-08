from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum

app = FastAPI()

class EstadoEnum(str, Enum):
    pendiente = "pendiente"
    en_proceso = "en_proceso"
    completada = "completada"

class TareaCrear(BaseModel):
    tipo: Literal["esperar", "calcular", "descargar"]
    prioridad: int = Field(default=1, ge=1, le=10)

class TareaActualizar(BaseModel):
    estado: Optional[EstadoEnum] = None

class Tarea(BaseModel):
    id: int
    tipo: str
    prioridad: int
    estado: EstadoEnum = EstadoEnum.pendiente

tareas_db: dict[int, Tarea] = {}
contador_id = 0

@app.post("/tareas", response_model=Tarea, status_code=status.HTTP_201_CREATED)
def crear_tarea(tarea_in: TareaCrear):
    global contador_id
    
    # 3. Rechazar si hay 10 o más pendientes con 429 Too Many Requests o 400 Bad Request
    pendientes = sum(1 for t in tareas_db.values() if t.estado == EstadoEnum.pendiente)
    if pendientes >= 10:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
            detail="Límite máximo de 10 tareas pendientes alcanzado. Intente más tarde."
        )

    contador_id += 1
    nueva = Tarea(id=contador_id, tipo=tarea_in.tipo, prioridad=tarea_in.prioridad)
    tareas_db[contador_id] = nueva
    return nueva

# 1. PATCH /tareas/{id} para actualizar parcialmente el estado
@app.patch("/tareas/{id_tarea}", response_model=Tarea)
def actualizar_tarea(id_tarea: int, datos: TareaActualizar):
    if id_tarea not in tareas_db:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    tarea = tareas_db[id_tarea]
    if datos.estado is not None:
        tarea.estado = datos.estado
    return tarea

# 2. GET /estadisticas
@app.get("/estadisticas")
def obtener_estadisticas():
    conteo = {e.value: 0 for e in EstadoEnum}
    for t in tareas_db.values():
        conteo[t.estado.value] += 1
    return {"total": len(tareas_db), "por_estado": conteo}