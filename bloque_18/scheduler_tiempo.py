import time
from collections import deque

def dormir(segundos):
    # Cede el timestamp exacto en el que la tarea desea despertar
    yield ("DORMIR", time.time() + segundos)

def tarea_con_espera(nombre, espera):
    print(f"[{nombre}] inicio espera {espera}s")
    yield from dormir(espera)
    print(f"[{nombre}] fin espera")

def scheduler_tiempo(tareas):
    pendientes = deque(tareas)
    dormidas = []  # Lista de (despertar_at, tarea)

    while pendientes or dormidas:
        ahora = time.time()
        
        # 1. Despertar tareas cuyo tiempo expiró
        dormidas_restantes = []
        for despertar_at, t in dormidas:
            if ahora >= despertar_at:
                pendientes.append(t)
            else:
                dormidas_restantes.append((despertar_at, t))
        dormidas = dormidas_restantes

        # 2. Ejecutar una tarea lista
        if pendientes:
            t = pendientes.popleft()
            try:
                msg = next(t)
                if isinstance(msg, tuple) and msg[0] == "DORMIR":
                    dormidas.append((msg[1], t))
                else:
                    pendientes.append(t)
            except StopIteration:
                pass
        else:
            time.sleep(0.001)  # Evitar busy-waiting si solo hay tareas dormidas