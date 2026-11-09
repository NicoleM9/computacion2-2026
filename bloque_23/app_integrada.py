from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from celery import Celery
from celery.result import AsyncResult

# 1. Configuración del cliente Celery
celery_app = Celery(
    "modulo_tareas",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)

# Tarea Celery (debe coincidir con la registrada en los workers)
@celery_app.task(name="tareas.procesar_trabajo")
def procesar_trabajo(segundos: int):
    import time
    time.sleep(segundos)
    return f"Trabajo de {segundos}s completado con éxito"


# 2. Configuración de FastAPI
app = FastAPI(title="API integrada con Celery")

class TrabajoReq(BaseModel):
    segundos: int = 10

class TrabajoResp(BaseModel):
    id: str
    estado: str
    resultado: str | None = None


@app.post("/trabajos", status_code=status.HTTP_202_ACCEPTED)
async def crear_trabajo(req: TrabajoReq):
    # Encolar la tarea asincrónicamente en Celery
    task = celery_app.send_task("tareas.procesar_trabajo", args=[req.segundos])
    return {"id": task.id, "estado": "PENDING", "mensaje": "Trabajo encolado exitosamente"}


@app.get("/trabajos/{id_trabajo}", response_model=TrabajoResp)
async def obtener_estado_trabajo(id_trabajo: str):
    res = AsyncResult(id_trabajo, app=celery_app)
    
    estado = res.state
    resultado_val = None
    
    if res.ready():
        if res.successful():
            resultado_val = str(res.result)
        else:
            resultado_val = f"Error: {str(res.result)}"
            
    return TrabajoResp(id=id_trabajo, estado=estado, resultado=resultado_val)