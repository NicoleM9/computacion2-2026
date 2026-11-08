from collections import deque

def tarea(nombre, pasos):
    for i in range(1, pasos + 1):
        print(f"[{nombre}] paso {i}/{pasos}")
        yield

def scheduler(tareas):
    pendientes = deque(tareas)
    reanudaciones = 0
    while pendientes:
        t = pendientes.popleft()
        try:
            reanudaciones += 1
            next(t)
            pendientes.append(t)  # Si no terminó, vuelve a la cola
        except StopIteration:
            pass  # Tarea finalizada
    print(f"Total de reanudaciones (next): {reanudaciones}")

if __name__ == '__main__':
    t1 = tarea("T1", 3)
    t2 = tarea("T2", 2)
    t3 = tarea("T3", 4)
    scheduler([t1, t2, t3])