from src import procfs

def analizar_memoria(pids):
    resultado = {}
    for pid in pids:
        status = procfs.leer_proc_status(pid)
        st = procfs.leer_proc_stat(pid)
        segmentos = procfs.leer_maps_segmentos(pid)
        
        resultado[pid] = {
            "vmsize": status.get("VmSize", "0 kB"),
            "vmrss": status.get("VmRSS", "0 kB"),
            "vmdata": status.get("VmData", "0 kB"),
            "vmstk": status.get("VmStk", "0 kB"),
            "vmexe": status.get("VmExe", "0 kB"),
            "vmlib": status.get("VmLib", "0 kB"),
            "vmhwm": status.get("VmHWM", "0 kB"),
            "vmswap": status.get("VmSwap", "0 kB"),
            "minflt": st["minflt"] if st else 0,
            "majflt": st["majflt"] if st else 0,
            "segmentos_kb": segmentos
        }
    return resultado
