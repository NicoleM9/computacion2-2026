import os
import sys

# Agregar la raíz al path para no tener problemas de importación
sys.path.insert(0, os.path.abspath("."))

from src.procfs import (
    get_all_pids,
    parse_stat,
    parse_status,
    parse_cmdline,
    parse_fds,
    parse_threads,
    decode_signal_mask,
    parse_system_global,
)

def test_procfs():
    print("=== TEST 1: Lista de PIDs ===")
    pids = get_all_pids()
    print(f"PIDs encontrados: {len(pids)} (Primeros 5: {pids[:5]})\n")

    # Usamos nuestro propio PID para la prueba (garantiza que exista y tengamos permisos)
    my_pid = os.getpid()
    print(f"=== TEST 2: Leyendo nuestro propio proceso (PID {my_pid}) ===")
    
    # 1. stat
    stat = parse_stat(my_pid)
    print(f"[parse_stat] Comm: {stat.get('comm') if stat else 'Error'}, State: {stat.get('state') if stat else 'Error'}")

    # 2. status
    status = parse_status(my_pid)
    print(f"[parse_status] RSS: {status.get('VmRSS') if status else 'Error'}, Uid: {status.get('uid') if status else 'Error'}")

    # 3. cmdline
    cmd = parse_cmdline(my_pid)
    print(f"[parse_cmdline]: {cmd}")

    # 4. FDs
    fds = parse_fds(my_pid)
    print(f"[parse_fds] FDs abiertos: {len(fds)}")
    for fd in fds[:3]:  # Mostrar los primeros 3
        print(f"   FD {fd['fd']} -> {fd['target']} ({fd['type']})")

    # 5. Threads
    threads = parse_threads(my_pid)
    print(f"[parse_threads] Cantidad de hilos: {len(threads)}")

    # 6. Máscaras de señales
    print("\n=== TEST 3: Decodificación de Señales ===")
    sig_example = decode_signal_mask("0000000000000002") # Bit 2 es SIGINT
    print(f"Máscara '0000000000000002' decodificada como: {sig_example}")

    # 7. Sistema Global
    print("\n=== TEST 4: Stats Globales del Sistema ===")
    sys_global = parse_system_global()
    print(f"Load average: {sys_global.get('loadavg')}")
    print(f"MemTotal: {sys_global.get('mem_total')}, MemFree: {sys_global.get('mem_free')}")

if __name__ == "__main__":
    test_procfs()
