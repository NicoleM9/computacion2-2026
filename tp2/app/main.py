"""API FastAPI. El apagado ordenado vive en el lifespan (uvicorn lo dispara
con SIGTERM y SIGINT)."""
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from . import config, persistencia
from .modelos import Estado, NuevaTarea
from .pool import ColaLlena, PoolCerrado, PoolTareas, TareaTerminada

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    persistencia.reportar_previo(config.DIR_VOLCADOS)
    pool = PoolTareas(config.NUM_WORKERS, config.TAMANO_COLA)
    await pool.iniciar()
    app.state.pool = pool
    if config.MODO_BLOQUEANTE:
        log.warning("MODO_BLOQUEANTE activo: hashear bloquea el event loop")
    yield
    log.info("Señal de apagado recibida")
    await pool.detener(config.LIMITE_APAGADO)
    # Se vuelca ANTES de liberar recursos: si algo se cuelga después, el estado ya está.
    persistencia.volcar([t.a_dict() for t in pool.tareas.values()],
                        config.DIR_VOLCADOS)
    await pool.liberar_recursos()


app = FastAPI(title="Plataforma de tareas distribuidas", lifespan=lifespan)


def _pool() -> PoolTareas:
    return app.state.pool


@app.post("/tareas", status_code=202)
async def crear_tarea(body: NuevaTarea):
    try:
        t = _pool().encolar(body.tipo, body.parametros, body.timeout)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except PoolCerrado:
        raise HTTPException(503, "el servicio se está apagando")
    except ColaLlena:
        raise HTTPException(429, "cola llena, reintentar más tarde")
    return {"id": t.id, "estado": t.estado.value}


@app.get("/tareas")
async def listar_tareas(estado: Estado | None = None):
    return [t.a_dict() for t in _pool().tareas.values()
            if estado is None or t.estado is estado]


@app.get("/tareas/{id}")
async def obtener_tarea(id: str):
    t = _pool().tareas.get(id)
    if t is None:
        raise HTTPException(404, "tarea inexistente")
    return t.a_dict()


@app.delete("/tareas/{id}")
async def cancelar_tarea(id: str):
    try:
        t = await _pool().cancelar(id)
    except KeyError:
        raise HTTPException(404, "tarea inexistente")
    except TareaTerminada:
        return JSONResponse({"detail": "la tarea ya terminó"}, status_code=409)
    return t.a_dict()


@app.get("/estadisticas")
async def estadisticas():
    return _pool().estadisticas()


if __name__ == "__main__":  # imprescindible para ProcessPoolExecutor en macOS/Windows
    uvicorn.run(app, host="0.0.0.0", port=8000)