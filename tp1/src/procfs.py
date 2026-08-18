import os

def obtener_pids():
    """Retorna una lista con todos los PIDs numéricos activos en /proc."""
    try:
        return [int(e) for e in os.listdir('/proc') if e.isdigit()]
    except Exception:
        return []

def leer_proc_sched_policy(pid):
    """Obtiene la política de planificación de /proc/[pid]/sched como fallback."""
    try:
        with open(f'/proc/{pid}/sched', 'r') as f:
            for line in f:
                if 'policy' in line and ':' in line:
                    return int(line.split(':')[1].strip())
    except Exception:
        pass
    return None

def leer_proc_stat(pid):
    """Parsea /proc/[pid]/stat para obtener datos básicos, métricas y política de scheduling."""
    try:
        with open(f'/proc/{pid}/stat', 'r') as f:
            content = f.read() # Una sola lectura
            
        rpar = content.rfind(')')
        if rpar == -1:
            return None
            
        idx_open = content.find('(')
        comm = content[idx_open + 1:rpar]
        rest = content[rpar + 2:].split()
        
        # Mapeo exacto desplazando el nombre (comm):
        # rest[0]: state (campo 3)
        # rest[1]: ppid (campo 4)
        # rest[2]: pgrp (campo 5)
        # rest[3]: session (campo 6)
        # rest[7]: minflt (campo 10)
        # rest[9]: majflt (campo 12)
        # rest[11]: utime (campo 14)
        # rest[12]: stime (campo 15)
        # rest[15]: priority (campo 18)
        # rest[16]: nice (campo 19)
        # rest[17]: num_threads (campo 20)
        # rest[37]: rt_priority (campo 40)
        # rest[38]: policy (campo 41)
        
        policy_val = int(rest[38]) if len(rest) > 38 else None
        if policy_val is None:
            policy_val = leer_proc_sched_policy(pid) or 0

        return {
            "pid": pid,
            "comm": comm,
            "state": rest[0],
            "ppid": int(rest[1]),
            "pgrp": int(rest[2]),
            "session": int(rest[3]),
            "minflt": int(rest[7]),
            "majflt": int(rest[9]),
            "utime": float(rest[11]),
            "stime": float(rest[12]),
            "priority": int(rest[15]),
            "nice": int(rest[16]),
            "num_threads": int(rest[17]),
            "rt_priority": int(rest[37]) if len(rest) > 37 else 0,
            "policy": policy_val
        }
    except Exception:
        return None

def leer_proc_status(pid):
    """Parsea /proc/[pid]/status devolviendo un diccionario de clave/valor."""
    status = {}
    try:
        with open(f'/proc/{pid}/status', 'r') as f:
            for line in f:
                if ':' in line:
                    k, v = line.split(':', 1)
                    status[k.strip()] = v.strip()
    except Exception:
        pass
    return status

def leer_proc_cmdline(pid):
    """Lee el comando completo ejecutado de /proc/[pid]/cmdline."""
    try:
        with open(f'/proc/{pid}/cmdline', 'rb') as f:
            content = f.read().decode('utf-8', errors='replace')
            cmd = content.replace('\x00', ' ').strip()
            return cmd if cmd else ""
    except Exception:
        return ""

def leer_fds_detalle(pid):
    """Retorna lista de FDs abiertos, el destino del symlink y su tipo inferido."""
    fds = []
    path_fd = f'/proc/{pid}/fd'
    try:
        for fd_num in os.listdir(path_fd):
            fd_path = os.path.join(path_fd, fd_num)
            try:
                target = os.readlink(fd_path)
                tipo = "file"
                if target.startswith("socket:"):
                    tipo = "socket"
                elif target.startswith("pipe:"):
                    tipo = "pipe"
                elif target.startswith("/dev/pts") or target.startswith("/dev/tty"):
                    tipo = "tty"
                fds.append({"fd": fd_num, "target": target, "type": tipo})
            except OSError:
                continue
    except Exception:
        pass
    return fds

def leer_threads_detalle(pid):
    """Lee los LWPs/Threads desde /proc/[pid]/task/."""
    threads = []
    task_dir = f'/proc/{pid}/task'
    try:
        for tid in os.listdir(task_dir):
            if not tid.isdigit():
                continue
            stat_path = f'{task_dir}/{tid}/stat'
            comm_path = f'{task_dir}/{tid}/comm'
            
            name = ""
            if os.path.exists(comm_path):
                try:
                    with open(comm_path, 'r') as f:
                        name = f.read().strip()
                except Exception:
                    pass
            
            state = "?"
            utime = 0.0
            stime = 0.0
            if os.path.exists(stat_path):
                try:
                    with open(stat_path, 'r') as f:
                        c = f.read()
                        rpar = c.rfind(')')
                        rest = c[rpar + 2:].split()
                        state = rest[0]
                        utime = float(rest[11])
                        stime = float(rest[12])
                except Exception:
                    pass
                    
            threads.append({
                "tid": int(tid),
                "name": name,
                "state": state,
                "utime": utime,
                "stime": stime
            })
    except Exception:
        pass
    return threads

def leer_maps_segmentos(pid):
    """Agrupa mapas de memoria (/proc/[pid]/maps) por segmentos."""
    segmentos = {"text": 0, "data": 0, "heap": 0, "stack": 0, "shared": 0}
    try:
        with open(f'/proc/{pid}/maps', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) < 1:
                    continue
                rango = parts[0].split('-')
                start = int(rango[0], 16)
                end = int(rango[1], 16)
                size_kb = (end - start) // 1024
                
                path = parts[-1] if len(parts) >= 6 else ""
                
                if "[heap]" in path:
                    segmentos["heap"] += size_kb
                elif "[stack]" in path:
                    segmentos["stack"] += size_kb
                elif "r-xp" in parts[1]:
                    segmentos["text"] += size_kb
                elif "rw-p" in parts[1]:
                    segmentos["data"] += size_kb
                elif "s" in parts[1]:
                    segmentos["shared"] += size_kb
    except Exception:
        pass
    return segmentos

def leer_meminfo():
    """Parsea /proc/meminfo para obtener métricas globales de memoria en KB."""
    mem = {}
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split(':')
                if len(parts) == 2:
                    k = parts[0].strip()
                    val_str = parts[1].strip().split()[0]
                    mem[k] = float(val_str)
    except Exception:
        pass
    return mem

def leer_uptime():
    """Lee el tiempo encendido del sistema en segundos desde /proc/uptime."""
    try:
        with open('/proc/uptime', 'r') as f:
            return float(f.read().split()[0])
    except Exception:
        return 0.0
    
# ==============================================================================
# ALIAS Y FUNCIONES COMPATIBLES CON EL ARCHIVO DE TESTS
# ==============================================================================

# 1. get_all_pids
get_all_pids = obtener_pids

# 2. parse_stat
parse_stat = leer_proc_stat

# 3. parse_status
def parse_status(pid):
    status = leer_proc_status(pid)
    if not status:
        return {}
    # Asegurar que devuelva 'uid' en minúscula si el test lo busca como status.get('uid')
    if "Uid" in status and "uid" not in status:
        status["uid"] = status["Uid"].split()[0]
    return status

# 4. parse_cmdline
parse_cmdline = leer_proc_cmdline

# 5. parse_fds
parse_fds = leer_fds_detalle

# 6. parse_threads
parse_threads = leer_threads_detalle

# 7. decode_signal_mask
def decode_signal_mask(hex_str):
    from src.analizadores.senales import decodificar_mascara_hex
    return decodificar_mascara_hex(hex_str)

# 8. parse_system_global
def parse_system_global():
    mem = leer_meminfo()
    uptime = leer_uptime()
    loadavg = "N/A"
    try:
        with open('/proc/loadavg', 'r') as f:
            loadavg = f.read().strip()
    except Exception:
        pass
    return {
        "uptime": uptime,
        "loadavg": loadavg,
        "mem_total": mem.get("MemTotal", 0),
        "mem_free": mem.get("MemFree", 0),
        "memoria_global": mem
    }