from src import procfs

def analizar_resumen(pids):
    resultado = []
    for pid in pids:
        st = procfs.leer_proc_stat(pid)
        if not st:
            continue
        status = procfs.leer_proc_status(pid)
        cmdline = procfs.leer_proc_cmdline(pid)
        
        uid = status.get("Uid", "").split()[0] if "Uid" in status else "N/A"
        vm_rss = status.get("VmRSS", "0 kB")
        
        resultado.append({
            "pid": pid,
            "ppid": st["ppid"],
            "comm": st["comm"],
            "cmdline": cmdline if cmdline else st["comm"],
            "state": st["state"],
            "uid": uid,
            "threads": st["num_threads"],
            "vm_rss": vm_rss,
            "utime": st["utime"],
            "stime": st["stime"]
        })
    return resultado
