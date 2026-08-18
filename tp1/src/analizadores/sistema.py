from src import procfs

def analizar_sistema(pids):
    mem = procfs.leer_meminfo()
    uptime = procfs.leer_uptime()
    
    loadavg = "N/A"
    try:
        with open('/proc/loadavg', 'r') as f:
            loadavg = f.read().strip()
    except Exception:
        pass

    estados = {"R": 0, "S": 0, "D": 0, "Z": 0, "T": 0, "Otros": 0}
    for pid in pids:
        st = procfs.leer_proc_stat(pid)
        if st:
            e = st["state"]
            if e in estados:
                estados[e] += 1
            else:
                estados["Otros"] += 1

    return {
        "uptime": uptime,
        "loadavg": loadavg,
        "memoria_global": mem,
        "totales_pids": len(pids),
        "conteo_estados": estados
    }