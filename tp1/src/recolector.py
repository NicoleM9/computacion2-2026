import os
import time
import multiprocessing as mp

# Historial local para cálculo de CPU %
prev_cpu_times = {}

SCHED_POLICIES = {
    0: "SCHED_OTHER",
    1: "SCHED_FIFO",
    2: "SCHED_RR",
    3: "SCHED_BATCH",
    5: "SCHED_IDLE",
    6: "SCHED_DEADLINE"
}

# --- FUNCIONES DE LECTURA DE /proc ---

def get_system_uptime():
    try:
        with open("/proc/uptime", "r") as f:
            return float(f.read().split()[0])
    except Exception:
        return 0.0

def get_system_loadavg():
    try:
        with open("/proc/loadavg", "r") as f:
            parts = f.read().split()
            return f"{parts[0]} {parts[1]} {parts[2]}"
    except Exception:
        return "N/A"

def obtener_pids():
    pids = []
    try:
        for entry in os.listdir("/proc"):
            if entry.isdigit():
                pids.append(int(entry))
    except Exception:
        pass
    return pids

def calcular_cpu_porcentaje(pid, utime_ticks, stime_ticks):
    global prev_cpu_times
    now = time.time()
    total_ticks = utime_ticks + stime_ticks
    clk_tck = os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else 100.0
    cpu_percent = 0.0

    if pid in prev_cpu_times:
        prev_ticks, prev_time = prev_cpu_times[pid]
        delta_ticks = total_ticks - prev_ticks
        delta_time = now - prev_time

        if delta_time > 0:
            cpu_seconds = delta_ticks / clk_tck
            cpu_percent = (cpu_seconds / delta_time) * 100.0

    prev_cpu_times[pid] = (total_ticks, now)
    return round(max(0.0, cpu_percent), 1)

def parse_proc_stat(pid):
    try:
        with open(f"/proc/{pid}/stat", "r") as f:
            content = f.read().strip()
            
        rpar = content.rfind(')')
        if rpar == -1:
            return None
            
        comm = content[content.find('(')+1:rpar]
        rest = content[rpar+2:].split()
        
        policy_id = 0
        if len(rest) > 38:
            try:
                policy_id = int(rest[38])
            except ValueError:
                policy_id = 0

        return {
            "comm": comm,
            "state": rest[0],
            "ppid": int(rest[1]),
            "utime": int(rest[11]),
            "stime": int(rest[12]),
            "priority": int(rest[15]),
            "nice": int(rest[16]),
            "threads": int(rest[17]),
            "policy": SCHED_POLICIES.get(policy_id, f"UNKNOWN({policy_id})")
        }
    except Exception:
        return None

def parse_proc_status(pid):
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

def parse_cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "r") as f:
            content = f.read().replace('\x00', ' ').strip()
            return content if content else "[sin cmdline]"
    except Exception:
        return "[desconocido]"

def parse_proc_fds(pid):
    """Devuelve la lista formateada para los tests/trabajadores."""
    fds = []
    fd_dir = f"/proc/{pid}/fd"
    try:
        if os.path.exists(fd_dir):
            for fd_name in os.listdir(fd_dir):
                try:
                    target = os.readlink(os.path.join(fd_dir, fd_name))
                    fds.append({"fd": fd_name, "target": target, "type": "link"})
                except Exception:
                    fds.append({"fd": fd_name, "target": "desconocido", "type": "desconocido"})
    except Exception:
        pass
    return fds

def parse_threads(pid):
    threads = []
    task_dir = f"/proc/{pid}/task"
    try:
        if os.path.exists(task_dir):
            for tid in os.listdir(task_dir):
                if tid.isdigit():
                    threads.append(int(tid))
    except Exception:
        pass
    return threads

def decode_signal_mask(mask_hex):
    try:
        val = int(mask_hex, 16)
        signals = []
        for i in range(1, 32):
            if val & (1 << (i - 1)):
                signals.append(i)
        return signals
    except Exception:
        return []

def parse_system_global():
    mem_total = "0 kB"
    mem_free = "0 kB"
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_total = line.split(":", 1)[1].strip()
                elif line.startswith("MemFree:"):
                    mem_free = line.split(":", 1)[1].strip()
    except Exception:
        pass

    return {
        "uptime": get_system_uptime(),
        "loadavg": get_system_loadavg(),
        "mem_total": mem_total,
        "mem_free": mem_free
    }


# --- TRABAJADORES (WORKERS) PARA LOS PROCESOS HIJOS ---

def obtener_intervalo(interval_val):
    """Auxiliar para tolerar tanto floats simples como mp.Value."""
    if hasattr(interval_val, "value"):
        return interval_val.value
    return float(interval_val) if interval_val else 1.0

def worker_resumen(snapshot_dict, interval_val, running_flag):
    while running_flag.value:
        try:
            pids = obtener_pids()
            resumen_list = []
            for pid in pids:
                stat = parse_proc_stat(pid)
                if not stat:
                    continue
                status = parse_proc_status(pid)
                uid = status.get("Uid", "0").split()[0] if status else "0"
                vm_rss = status.get("VmRSS", "0 kB") if status else "0 kB"
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

            pids_set = set(pids)
            for old_pid in list(prev_cpu_times.keys()):
                if old_pid not in pids_set:
                    del prev_cpu_times[old_pid]

            snapshot_dict["resumen"] = resumen_list
        except Exception as e:
            pass
        time.sleep(obtener_intervalo(interval_val))

def worker_memoria(snapshot_dict, interval_val, running_flag):
    while running_flag.value:
        try:
            pids = obtener_pids()
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
        except Exception:
            pass
        time.sleep(obtener_intervalo(interval_val))

def worker_fds(snapshot_dict, interval_val, running_flag):
    while running_flag.value:
        try:
            pids = obtener_pids()
            fds_dict = {}
            for pid in pids[:100]:
                fds = parse_proc_fds(pid)
                fds_dict[pid] = {
                    "total_fds": len(fds),
                    "fds": [f"{f['fd']} -> {f['target']}" for f in fds[:20]]
                }
            snapshot_dict["fds"] = fds_dict
        except Exception:
            pass
        time.sleep(obtener_intervalo(interval_val))

def worker_threads(snapshot_dict, interval_val, running_flag):
    while running_flag.value:
        try:
            pids = obtener_pids()
            thr_dict = {}
            for pid in pids:
                stat = parse_proc_stat(pid)
                if stat:
                    thr_dict[pid] = {
                        "total_threads": stat["threads"]
                    }
            snapshot_dict["threads"] = thr_dict
        except Exception:
            pass
        time.sleep(obtener_intervalo(interval_val))

def worker_senales(snapshot_dict, interval_val, running_flag):
    while running_flag.value:
        try:
            pids = obtener_pids()
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
        except Exception:
            pass
        time.sleep(obtener_intervalo(interval_val))

def worker_scheduling(snapshot_dict, interval_val, running_flag):
    while running_flag.value:
        try:
            pids = obtener_pids()
            sch_dict = {}
            for pid in pids:
                stat = parse_proc_stat(pid)
                if stat:
                    sch_dict[pid] = {
                        "nice": str(stat["nice"]),
                        "priority": str(stat["priority"]),
                        "policy": stat["policy"]
                    }
            snapshot_dict["scheduling"] = sch_dict
        except Exception:
            pass
        time.sleep(obtener_intervalo(interval_val))

def worker_sistema(snapshot_dict, interval_val, running_flag):
    while running_flag.value:
        try:
            pids = obtener_pids()
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
        except Exception:
            pass
        time.sleep(obtener_intervalo(interval_val))

TRABAJADORES_ANALIZADORES = {
    "resumen": worker_resumen,
    "memoria": worker_memoria,
    "fds": worker_fds,
    "threads": worker_threads,
    "senales": worker_senales,
    "scheduling": worker_scheduling,
    "sistema": worker_sistema
}