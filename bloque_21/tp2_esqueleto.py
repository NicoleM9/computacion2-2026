import asyncio
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from enum import Enum
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

class TipoTarea(str, Enum):
    hashear = "hashear"
    esperar = "esperar"

class EstadoTarea(str, Enum):
    pendiente = "pendiente"
    ejecutando = "ejecutando"
    completada = "completada"
    cancelada = "cancelada"

class TareaCreate(BaseModel):
    tipo: TipoTarea
    parametro: int = 1

class TareaResponse(BaseModel):
    id: int
    tipo: TipoTarea
    estado: EstadoTarea
    resultado: Optional[str] = None

class TareaItem:
    def __init__(self, id_tarea: int, tipo: TipoTarea, parametro: int):
        self.id = id_tarea
        self.tipo = tipo
        self.parametro = parametro
        self.estado = EstadoTarea.pendiente
        self.resultado = None
        self.async_task: Optional[asyncio.Task] = None

# --- TRABAJO CPU-BOUND PARA EL EXECUTOR ---
def computo_pesado_hash(n: int) -> str:
    total = 0
    for i in range(n * 5_000_000):
        total += i * i
    return f"HashResult-{total}"

# --- ESTADO GLOBAL Y COMPONENTES ---
db_tareas: Dict[int, TareaItem] = {}
contador_ids = 0
cola_tareas: asyncio.Queue = None
executor_pool: ProcessPoolExecutor = None
workers_tasks = []
NUM_WORKERS = 3

async def worker(worker_id: int):
    loop = asyncio.get_running_loop()
    while True:
        item = await cola_tareas.get()
        if item is None: # Centinela de apagado
            cola_tareas.task_done()
            break
        
        if item.estado == EstadoTarea.cancelada:
            cola_tareas.task_done()
            continue

        item.estado = EstadoTarea.ejecutando
        item.async_task = asyncio.current_task()
        
        try:
            if item.tipo == TipoTarea.hashear:
                # Sacar trabajo CPU-bound del Event Loop
                res = await loop.run_in_executor(executor_pool, computo_pesado_hash, item.parametro)
                item.resultado = res
            elif item.tipo == TipoTarea.esperar:
                # Trabajo I/O-bound cooperativo en el Event Loop
                await asyncio.sleep(item.parametro)
                item.resultado = f"Esperado {item.parametro}s"
            
            item.estado = EstadoTarea.completada
        except asyncio.CancelledError:
            item.estado = EstadoTarea.cancelada
        except Exception as e:
            item.resultado = f"Error: {str(e)}"
            item.estado = EstadoTarea.completada
        finally:
            cola_tareas.task_done()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global cola_tareas, executor_pool, workers_tasks
    cola_tareas = asyncio.Queue(maxsize=100)
    executor_pool = ProcessPoolExecutor()
    
    # Arrancar workers en background
    workers_tasks = [asyncio.create_task(worker(i)) for i in range(NUM_WORKERS)]
    yield
    
    # APAGADO ORDENADO
    for _ in range(NUM_WORKERS):
        await cola_tareas.put(None)
    
    await asyncio.gather(*workers_tasks)
    executor_pool.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post("/tareas", response_model=TareaResponse, status_code=status.HTTP_202_ACCEPTED)
async def crear_tarea(t_in: TareaCreate):
    global contador_ids
    if cola_tareas.full():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servidor sobrecargado: cola llena"
        )
    
    contador_ids += 1
    item = TareaItem(contador_ids, t_in.tipo, t_in.parametro)
    db_tareas[contador_ids] = item
    await cola_tareas.put(item)
    
    return TareaResponse(id=item.id, tipo=item.tipo, estado=item.estado)

@app.get("/tareas/{id_tarea}", response_model=TareaResponse)
async def obtener_tarea(id_tarea: int):
    if id_tarea not in db_tareas:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    item = db_tareas[id_tarea]
    return TareaResponse(id=item.id, tipo=item.tipo, estado=item.estado, resultado=item.resultado)

@app.delete("/tareas/{id_tarea}")
async def cancelar_tarea(id_tarea: int):
    if id_tarea not in db_tareas:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    item = db_tareas[id_tarea]
    if item.estado == EstadoTarea.pendiente:
        item.estado = EstadoTarea.cancelada
    elif item.estado == EstadoTarea.ejecutando and item.async_task:
        item.async_task.cancel()
        item.estado = EstadoTarea.cancelada
    
    return {"mensaje": f"Tarea {id_tarea} cancelada"}