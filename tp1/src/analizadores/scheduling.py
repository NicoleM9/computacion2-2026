from src import procfs

POLITICAS_SCHED = {
    0: "SCHED_OTHER",
    1: "SCHED_FIFO",
    2: "SCHED_RR",
    3: "SCHED_BATCH",
    5: "SCHED_IDLE"
}

def analizar_scheduling(pids):
    resultado = {}
    for pid in pids:
        st = procfs.leer_proc_stat(pid)
        status = procfs.leer_proc_status(pid)
        
        if not st:
            continue
            
        policy_num = st.get("policy", 0)
        policy_str = POLITICAS_SCHED.get(policy_num, f"UNKNOWN({policy_num})")
        
        resultado[pid] = {
            "nice": st["nice"],
            "priority": st["priority"],
            "policy": policy_str,
            "rt_priority": st["rt_priority"],
            "cpu_affinity": status.get("Cpus_allowed_list", "N/A"),
            "pgrp": st["pgrp"],
            "session": st["session"],
            "voluntary_ctxt_switches": status.get("voluntary_ctxt_switches", "0"),
            "nonvoluntary_ctxt_switches": status.get("nonvoluntary_ctxt_switches", "0")
        }
    return resultado
