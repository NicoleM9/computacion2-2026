from src import procfs

def analizar_fds(pids):
    resultado = {}
    for pid in pids:
        fds = procfs.leer_fds_detalle(pid)
        resultado[pid] = {
            "total_fds": len(fds),
            "fds": fds
        }
    return resultado
