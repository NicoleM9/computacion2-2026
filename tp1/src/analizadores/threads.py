from src import procfs

def analizar_threads(pids):
    resultado = {}
    for pid in pids:
        status = procfs.leer_proc_status(pid)
        threads = procfs.leer_threads_detalle(pid)
        
        resultado[pid] = {
            "total_threads": len(threads),
            "voluntary_ctxt_switches": status.get("voluntary_ctxt_switches", "0"),
            "nonvoluntary_ctxt_switches": status.get("nonvoluntary_ctxt_switches", "0"),
            "threads_list": threads
        }
    return resultado
