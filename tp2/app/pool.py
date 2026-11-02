"""Cola + pool de workers (corrutinas), cancelación, timeouts y apagado."""
from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager

from . import config, ejecutores
from .modelos import TERMINALES, Estado, Tarea

log = logging.getLogger("pool")


class PoolCerrado(Exception):
    """El sistema se está apagando: no se aceptan tareas."""


class ColaLlena(Exception):
    """La cola alcanzó su maxsize."""


class TareaTerminada(Exception):
    """Se intentó cancelar una tarea que ya terminó."""


class PoolTareas:
    def __init__(self, n_workers: int, tam_cola: int):
        self.n_workers = n_workers
        self.tareas: dict[str, Tarea] = {}
        self.cola: asyncio.Queue[Tarea] = asyncio.Queue(maxsize=tam_cola)
        self.cerrado = False
        self.ocupados = 0
        self._workers: list[asyncio.Task] = []
        self._proc: ProcessPoolExecutor | None = None
        self._manager = None

    # ------------------------------------------------------------ ciclo de vida
    async def iniciar(self) -> None:
        self._proc = ProcessPoolExecutor(max_workers=config.MAX_PROCESOS)
        self._manager = Manager()
        self._workers = [asyncio.create_task(self._worker(i), name=f"worker-{i}")
                         for i in range(self.n_workers)]
        log.info("Pool iniciado: %d workers, %d procesos CPU, cola máx %d",
                 self.n_workers, config.MAX_PROCESOS, self.cola.maxsize)

    async def detener(self, limite: float) -> None:
        """Fase 1: deja de aceptar, espera (con límite) y cancela lo que quede."""
        self.cerrado = True
        log.info("Apagado: esperando hasta %.0fs a las tareas en curso", limite)
        try:
            await asyncio.wait_for(self.cola.join(), limite)
            log.info("Todas las tareas terminaron dentro del límite")
        except asyncio.TimeoutError:
            log.warning("Límite vencido: se cancela lo que quede")

        # Lo pendiente se descarta (los workers lo saltarán al sacarlo).
        descartadas = 0
        for t in self.tareas.values():
            if t.estado is Estado.PENDIENTE:
                self._finalizar(t, Estado.CANCELADA, error="apagado del servicio")
                descartadas += 1
        en_curso = [t._task for t in self.tareas.values()
                    if t.estado is Estado.EJECUTANDO and t._task]
        log.info("Cancelando %d tareas en ejecución; %d pendientes descartadas",
                 len(en_curso), descartadas)
        for w in self._workers:
            w.cancel()
        try:  # espera acotada: el apagado nunca debe quedar colgado
            await asyncio.wait_for(
                asyncio.gather(*self._workers, *en_curso, return_exceptions=True), 5)
        except asyncio.TimeoutError:
            log.error("Hay tareas que no respondieron a la cancelación")
        log.info("Workers y tareas detenidos")

    async def liberar_recursos(self) -> None:
        """Fase 2 (después de volcar el estado): procesos y manager."""
        self._proc.shutdown(wait=False, cancel_futures=True)
        try:
            await asyncio.wait_for(asyncio.to_thread(self._manager.shutdown), 5)
        except asyncio.TimeoutError:
            log.warning("El manager no cerró a tiempo")
        log.info("Recursos liberados")

    # --------------------------------------------------------------- operaciones
    def encolar(self, tipo: str, parametros: dict, timeout: float | None) -> Tarea:
        if self.cerrado:
            raise PoolCerrado()
        ejecutores.validar(tipo, parametros)  # ValueError -> 422
        tarea = Tarea(tipo=tipo, parametros=parametros,
                      timeout=timeout or config.TIMEOUT_DEFECTO)
        try:
            self.cola.put_nowait(tarea)  # nunca bloquea el POST
        except asyncio.QueueFull:
            raise ColaLlena() from None
        self.tareas[tarea.id] = tarea
        return tarea

    async def cancelar(self, id_: str) -> Tarea:
        tarea = self.tareas[id_]  # KeyError -> 404
        if tarea.estado in TERMINALES:
            raise TareaTerminada()
        if tarea.estado is Estado.PENDIENTE:
            # asyncio.Queue no permite sacar del medio: se marca y el worker la salta.
            self._finalizar(tarea, Estado.CANCELADA, error="cancelada por el usuario")
        else:
            tarea._task.cancel()
            # Esperamos a que la limpieza termine antes de responder.
            await asyncio.gather(tarea._task, return_exceptions=True)
        return tarea

    def estadisticas(self) -> dict:
        por_estado = {e.value: 0 for e in Estado}
        esperas, ejecuciones = [], []
        for t in self.tareas.values():
            por_estado[t.estado.value] += 1
            if t.iniciada:
                esperas.append(t.iniciada - t.creada)
            if t.estado is Estado.COMPLETADA and t.iniciada and t.terminada:
                ejecuciones.append(t.terminada - t.iniciada)

        def prom(xs):
            return round(sum(xs) / len(xs), 4) if xs else None

        return {
            "tareas_por_estado": por_estado,
            "tiempo_promedio_espera_s": prom(esperas),
            "tiempo_promedio_ejecucion_s": prom(ejecuciones),
            "workers_ocupados": self.ocupados,
            "workers_total": self.n_workers,
            "tareas_en_cola": self.cola.qsize(),
        }

    # ------------------------------------------------------------------ internos
    @staticmethod
    def _finalizar(t: Tarea, estado: Estado, error: str | None = None) -> None:
        if t.estado in TERMINALES:  # idempotente
            return
        t.estado = estado
        t.error = error
        t.terminada = time.time()

    async def _despachar(self, t: Tarea):
        if t.tipo == "descargar":
            return await ejecutores.descargar(t.parametros)
        if t.tipo == "esperar":
            return await ejecutores.esperar(t.parametros)
        if t.tipo == "hashear":
            return await ejecutores.hashear(t.parametros, self._proc, self._manager)
        raise ValueError(f"tipo desconocido: {t.tipo}")

    async def _correr(self, t: Tarea) -> None:
        """Corre UNA tarea y deja su estado final. Es el asyncio.Task que
        cancela el DELETE: así el worker nunca muere por una cancelación."""
        try:
            t.resultado = await asyncio.wait_for(self._despachar(t), t.timeout)
            self._finalizar(t, Estado.COMPLETADA)
        except asyncio.TimeoutError:
            self._finalizar(t, Estado.FALLIDA, error=f"timeout tras {t.timeout}s")
        except asyncio.CancelledError:
            motivo = ("apagado del servicio" if self.cerrado
                      else "cancelada por el usuario")
            self._finalizar(t, Estado.CANCELADA, error=motivo)
            raise  # propagar: la cancelación nunca se traga
        except Exception as e:  # noqa: BLE001 - red de seguridad por tarea
            log.exception("Tarea %s falló", t.id)
            self._finalizar(t, Estado.FALLIDA, error=f"{type(e).__name__}: {e}")

    async def _worker(self, n: int) -> None:
        while True:
            tarea = await self.cola.get()
            try:
                if tarea.estado is Estado.CANCELADA:
                    continue  # fue cancelada mientras esperaba en la cola
                tarea.estado = Estado.EJECUTANDO
                tarea.iniciada = time.time()
                self.ocupados += 1
                tarea._task = asyncio.create_task(self._correr(tarea),
                                                  name=f"tarea-{tarea.id}")
                try:
                    await tarea._task
                except asyncio.CancelledError:
                    # cancelling() > 0 => cancelaron AL WORKER (apagado): propagar.
                    # Si es 0, cancelaron solo la tarea interna (DELETE): el
                    # worker sigue vivo y toma la próxima.
                    if asyncio.current_task().cancelling():
                        raise
                    self._finalizar(tarea, Estado.CANCELADA)
                finally:
                    self.ocupados -= 1
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 - el worker no debe morir jamás
                log.exception("Error inesperado en worker-%d", n)
            finally:
                self.cola.task_done()
