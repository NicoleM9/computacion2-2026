from src import procfs

NOMBRES_SENALES = {
    1: "SIGHUP", 2: "SIGINT", 3: "SIGQUIT", 6: "SIGABRT", 9: "SIGKILL",
    11: "SIGSEGV", 13: "SIGPIPE", 14: "SIGALRM", 15: "SIGTERM", 17: "SIGCHLD",
    18: "SIGCONT", 19: "SIGSTOP", 20: "SIGTSTP", 28: "SIGWINCH", 10: "SIGUSR1", 12: "SIGUSR2"
}

def decodificar_mascara_hex(hex_str):
    if not hex_str:
        return []
    try:
        val = int(hex_str, 16)
        senales = []
        for bit in range(1, 65):
            if (val >> (bit - 1)) & 1:
                senales.append(NOMBRES_SENALES.get(bit, f"SIG_{bit}"))
        return senales
    except ValueError:
        return []

def analizar_senales(pids):
    resultado = {}
    for pid in pids:
        status = procfs.leer_proc_status(pid)
        
        resultado[pid] = {
            "SigBlk": decodificar_mascara_hex(status.get("SigBlk", "0")),
            "SigIgn": decodificar_mascara_hex(status.get("SigIgn", "0")),
            "SigCgt": decodificar_mascara_hex(status.get("SigCgt", "0")),
            "SigPnd": decodificar_mascara_hex(status.get("SigPnd", "0")),
            "ShdPnd": decodificar_mascara_hex(status.get("ShdPnd", "0")),
            "raw_SigBlk": status.get("SigBlk", "0")
        }
    return resultado
