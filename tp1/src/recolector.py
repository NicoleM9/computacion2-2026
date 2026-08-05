import os
import time
import json
import glob
import multiprocessing as mp

# Diccionario local en el proceso recolector para recordar tiempos anteriores
# Estructura: { pid: (total_ticks_anterior, timestamp_anterior) }
prev_cpu_times = {}

def get_system_uptime():
    """Lee el uptime global del sistema desde /proc/uptime"""
    try:
        with open("/proc/uptime", "r") as f:
            return float(f.read().split()[0])
    except Exception:
        return 0.0

def get_system_loadavg():
    """Lee la carga del sistema desde /proc/loadavg"""
    try:
        with open("/proc/loadavg", "r") as f:
            parts = f.read().split()
            return f"{parts[0]} {parts[1]} {parts[2]}"
    except Exception:
        return "N/A"

def calcular_cpu_porcentaje(pid, utime_ticks, stime_ticks):
    """Calcula el % de CPU por diferencia entre lecturas consecutivas"""
    global prev_cpu_times
    now = time.time()
    total_ticks = utime_ticks + stime_ticks
    
    # Frecuencia de reloj del kernel (normalmente 100 Hz en Linux)
    clk_tck = os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else 100.0
    cpu_percent = 0.0

    if pid in prev_cpu_times:
        prev_ticks, prev_time = prev_cpu_times[pid]
        delta_ticks = total_ticks - prev_ticks
        delta_time = now - prev_time

        if delta_time > 0:
            cpu_seconds = delta_ticks / clk_tck
            cpu_percent = (cpu_seconds / delta_time) * 100.0

    # Actualizar historial
    prev_cpu_times[pid] = (total_ticks, now)
    return round(max(0.0, cpu_percent), 1)

def parse_proc_stat(pid):
    """Parsea /proc/[pid]/stat de forma segura considerando espacios en el comm"""
    try:
        with open(f"/proc/{pid}/stat", "r") as f:
            content = f.read().strip()
            
        # El campo 'comm' está entre paréntesis y puede contener espacios
        rpar = content.rfind(')')
        if rpar == -1:
            return None
            
        comm = content[content.find('(')+1:rpar]
        rest = content[rpar+2:].split()
        
        state = rest[0]
        ppid = int(rest[1])
        utime = int(rest[11])
        stime = int(rest[12])
        num_threads = int(rest[17])
        
        return {
            "comm": comm,
            "state": state,
            "ppid": ppid,
            "utime": utime,
            "stime": stime,
            "threads": num_threads
        }
    except Exception:
        return None

def parse_proc_status(pid):
    """Parsea /proc/[pid]/status para extraer UID, RSS y señales"""
    data = {}
    try:
        with open(f"/proc/{pid}/status", "r") as f:
            for line in f:
                if ":" in line:
                    key, val = line.split(":", 1)
                    data[key.strip()] = val.strip()
    except Exception:
        pass
    return data

def parse_proc_fds(pid):
    """Lista los File Descriptors abiertos de un proceso"""
    try:
        fds = []
        fd_dir = f"/proc/{pid}/fd"
        if os.path.exists(fd_dir):
            for fd_name in os.listdir(fd_dir):
                try:
                    target = os.readlink(os.path.join(fd_dir, fd_name))
                    fds.append(f"{fd_name} -> {target}")
                except Exception:
                    fds.append(fd_name)
        return fds
    except Exception:
        return []

def worker_recolector(snapshot_dict, intervals_dict, running_flag):
    """Worker principal que corre en un subproceso independiente recopilando métricas"""
    last_runs = {
        "resumen": 0, "memoria": 0, "fds": 0,
        "threads": 0, "senales": 0, "scheduling": 0, "sistema": 0
    }

    while running_flag.value:
        now = time.time()
        
        # 1. Obtener lista de PIDs activos en el sistema
        pids = []
        for entry in os.listdir("/proc"):
            if entry.isdigit():
                pids.append(int(entry))

        # ---------------- VISTA 1: RESUMEN ----------------
        int_resumen = intervals_dict["resumen"].value if "resumen" in intervals_dict else 2.0
        if now - last_runs["resumen"] >= int_resumen:
            resumen_list = []
            for pid in pids:
                stat = parse_proc_stat(pid)
                if not stat:
                    continue
                status = parse_proc_status(pid)
                
                # UID
                uid = status.get("Uid", "0").split()[0]
                
                # Memoria RSS
                vm_rss = status.get("VmRSS", "0 kB")
                
                # Porcentaje de CPU
                cpu_pct = calcular_cpu_porcentaje(pid, stat["utime"], stat["stime"])

                resumen_list.append({
                    "pid": pid,
                    "ppid": stat["ppid"],
                    "uid": uid,
                    "state": stat["state"],
                    "threads": stat["threads"],
                    "vm_rss": vm_rss,
                    "cpu": cpu_pct,
                    "comm": stat["comm"]
                })

            # Limpiar PIDs muertos del historial de CPU para ahorrar memoria
            pids_set = set(pids)
            for old_pid in list(prev_cpu_times.keys()):
                if old_pid not in pids_set:
                    del prev_cpu_times[old_pid]

            snapshot_dict["resumen"] = resumen_list
            last_runs["resumen"] = now

        # ---------------- VISTA 2: MEMORIA ----------------
        int_mem = intervals_dict["memoria"].value if "memoria" in intervals_dict else 3.0
        if now - last_runs["memoria"] >= int_mem:
            mem_dict = {}
            for pid in pids:
                status = parse_proc_status(pid)
                if status:
                    mem_dict[pid] = {
                        "vmsize": status.get("VmSize", "0 kB"),
                        "vmrss": status.get("VmRSS", "0 kB"),
                        "vmdata": status.get("VmData", "0 kB"),
                        "vmstk": status.get("VmStk", "0 kB"),
                        "vmexe": status.get("VmExe", "0 kB"),
                        "vmlib": status.get("VmLib", "0 kB")
                    }
            snapshot_dict["memoria"] = mem_dict
            last_runs["memoria"] = now

        # ---------------- VISTA 3: FILE DESCRIPTORS ----------------
        int_fds = intervals_dict["fds"].value if "fds" in intervals_dict else 5.0
        if now - last_runs["fds"] >= int_fds:
            fds_dict = {}
            for pid in pids[:100]:  # Escanear primeros 100 procesos para evitar sobrecarga de I/O
                fds = parse_proc_fds(pid)
                fds_dict[pid] = {
                    "total_fds": len(fds),
                    "fds": fds[:20]  # Mostrar primeros 20 FDs
                }
            snapshot_dict["fds"] = fds_dict
            last_runs["fds"] = now

        # ---------------- VISTA 4: THREADS ----------------
        int_thr = intervals_dict["threads"].value if "threads" in intervals_dict else 2.0
        if now - last_runs["threads"] >= int_thr:
            thr_dict = {}
            for pid in pids:
                stat = parse_proc_stat(pid)
                if stat:
                    thr_dict[pid] = {
                        "total_threads": stat["threads"]
                    }
            snapshot_dict["threads"] = thr_dict
            last_runs["threads"] = now

        # ---------------- VISTA 5: SEÑALES ----------------
        int_sig = intervals_dict["senales"].value if "senales" in intervals_dict else 10.0
        if now - last_runs["senales"] >= int_sig:
            sig_dict = {}
            for pid in pids:
                status = parse_proc_status(pid)
                if status:
                    sig_dict[pid] = {
                        "SigBlk": status.get("SigBlk", "0000000000000000"),
                        "SigIgn": status.get("SigIgn", "0000000000000000"),
                        "SigCgt": status.get("SigCgt", "0000000000000000"),
                        "SigPnd": status.get("SigPnd", "0000000000000000")
                    }
            snapshot_dict["senales"] = sig_dict
            last_runs["senales"] = now

        # ---------------- VISTA 6: SCHEDULING ----------------
        int_sch = intervals_dict["scheduling"].value if "scheduling" in intervals_dict else 10.0
        if now - last_runs["scheduling"] >= int_sch:
            sch_dict = {}
            for pid in pids:
                try:
                    with open(f"/proc/{pid}/stat", "r") as f:
                        parts = f.read().split()
                        # nice: campo 18, priority: campo 17 (base 0)
                        rpar = f.read().rfind(')')
                        rest = parts[rpar:] if rpar != -1 else parts[2:]
                        nice = parts[18] if len(parts) > 18 else "0"
                        priority = parts[17] if len(parts) > 17 else "0"
                        
                        sch_dict[pid] = {
                            "nice": nice,
                            "priority": priority,
                            "policy": "SCHED_OTHER"
                        }
                except Exception:
                    pass
            snapshot_dict["scheduling"] = sch_dict
            last_runs["scheduling"] = now

        # ---------------- VISTA 7: SISTEMA GLOBAL ----------------
        int_sys = intervals_dict["sistema"].value if "sistema" in intervals_dict else 1.0
        if now - last_runs["sistema"] >= int_sys:
            estados = {"R": 0, "S": 0, "D": 0, "Z": 0, "T": 0, "Otros": 0}
            for pid in pids:
                stat = parse_proc_stat(pid)
                if stat:
                    st = stat["state"]
                    if st in estados:
                        estados[st] += 1
                    else:
                        estados["Otros"] += 1

            snapshot_dict["sistema"] = {
                "uptime": get_system_uptime(),
                "loadavg": get_system_loadavg(),
                "totales_pids": len(pids),
                "conteo_estados": estados
            }
            last_runs["sistema"] = now

        # Pequeña pausa para no saturar el core de CPU
        time.sleep(0.1)
