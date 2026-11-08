import asyncio
import time
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from fastapi import FastAPI

def trabajo_pesado(n: int = 30_000_000) -> int:
    """Cálculo CPU-bound intensivo."""
    total = 0
    for i in range(n):
        total += i * i
    return total

pool: ProcessPoolExecutor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = ProcessPoolExecutor()
    yield
    pool.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/tareas")
async def obtener_tareas():
    return {"status": "ok"}

@app.post("/hashear-sin-executor")
async def hashear_sin_executor():
    res = trabajo_pesado()
    return {"resultado": res}

@app.post("/hashear-con-executor")
async def hashear_con_executor():
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(pool, trabajo_pesado)
    return {"resultado": res}