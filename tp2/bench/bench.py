"""Mediciones del TP. Solo librería estándar: corre en tu máquina, no en Docker.

Uso (desde la carpeta del proyecto, con `docker compose up` andando):
    python3 bench/bench.py m1        # medición 1: secuencial vs concurrente
    python3 bench/bench.py m3        # medición 3A: techo del pool de workers
    python3 bench/bench.py m3b       # medición 3B: techo de conexiones en 'descargar'
    python3 bench/bench.py rafaga    # qué pasa con una ráfaga de miles de tareas
"""
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request

API = os.getenv("API_URL", "http://localhost:8000")
# URL del servidor de latencia VISTA DESDE el contenedor de la API.
LAT = os.getenv("LATENCIA_URL", "http://latencia:8080")
TERMINALES = {"completada", "fallida", "cancelada"}


def api(metodo, ruta, cuerpo=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(API + ruta, data=datos, method=metodo,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def crear(tipo, parametros, timeout=None):
    cuerpo = {"tipo": tipo, "parametros": parametros}
    if timeout:
        cuerpo["timeout"] = timeout
    return api("POST", "/tareas", cuerpo)


def esperar_fin(ids, intervalo=0.05):
    """Espera a que TODAS las tareas terminen. Devuelve {id: tarea}."""
    pendientes, listas = set(ids), {}
    while pendientes:
        for i in list(pendientes):
            _, t = api("GET", f"/tareas/{i}")
            if t["estado"] in TERMINALES:
                listas[i] = t
                pendientes.discard(i)
        if pendientes:
            time.sleep(intervalo)
    return listas


def latencia_get():
    t0 = time.perf_counter()
    api("GET", "/tareas")
    return time.perf_counter() - t0


def p(*a):
    print(*a, flush=True)


# ------------------------------------------------------------ medición 1
def m1(reps=3, n=20, delay=1):
    url = f"{LAT}/delay/{delay}"
    p(f"MEDICIÓN 1: {n} descargas de {url} (cada una tarda ~{delay}s en el servidor)")
    sec, conc, pool = [], [], []
    for r in range(1, reps + 1):
        # A) secuencial: una tarea por URL, esperando a que termine cada una
        t0 = time.perf_counter()
        for _ in range(n):
            _, t = crear("descargar", {"urls": [url]})
            esperar_fin([t["id"]], intervalo=0.02)
        sec.append(time.perf_counter() - t0)

        # B) concurrente: UNA tarea con las n URLs (asyncio.gather)
        t0 = time.perf_counter()
        _, t = crear("descargar", {"urls": [url] * n})
        fin = esperar_fin([t["id"]], intervalo=0.02)[t["id"]]
        conc.append(time.perf_counter() - t0)
        assert fin["estado"] == "completada", fin

        # C) n tareas de 1 URL a la vez: las reparte el pool de workers
        t0 = time.perf_counter()
        ids = [crear("descargar", {"urls": [url]})[1]["id"] for _ in range(n)]
        esperar_fin(ids)
        pool.append(time.perf_counter() - t0)
        p(f"  rep {r}: secuencial={sec[-1]:.2f}s  concurrente={conc[-1]:.2f}s  "
          f"{n} tareas por el pool={pool[-1]:.2f}s")
    ms, mc, mp = (statistics.median(x) for x in (sec, conc, pool))
    p("\nRESULTADO (mediana de las repeticiones)")
    p(f"  A) {n} descargas secuenciales .......... {ms:.2f} s")
    p(f"  B) {n} descargas concurrentes (1 tarea) . {mc:.2f} s")
    p(f"  C) {n} tareas de 1 URL por el pool ...... {mp:.2f} s")
    p(f"  Speedup B vs A: {ms / mc:.1f}x")


# ------------------------------------------------------------ medición 3A
def m3(duracion=0.5, tamanos=(4, 8, 16, 32, 64, 128, 256, 512)):
    p(f"MEDICIÓN 3A: M tareas 'esperar' de {duracion}s lanzadas a la vez")
    _, est = api("GET", "/estadisticas")
    w = est["workers_total"]
    p(f"workers del pool: {w}   (tiempo ideal = ceil(M/{w}) * {duracion}s)\n")
    p(f"{'M':>5} {'total(s)':>9} {'ideal(s)':>9} {'espera media(s)':>16} "
      f"{'espera máx(s)':>14} {'GET /tareas(ms)':>16}")
    for m in tamanos:
        t0 = time.perf_counter()
        ids = [crear("esperar", {"segundos": duracion})[1]["id"] for _ in range(m)]
        fin = esperar_fin(ids, intervalo=0.2)
        total = time.perf_counter() - t0
        esperas = [t["iniciada"] - t["creada"] for t in fin.values()]
        ideal = -(-m // w) * duracion
        lat = latencia_get() * 1000
        p(f"{m:>5} {total:>9.2f} {ideal:>9.2f} {statistics.mean(esperas):>16.2f} "
          f"{max(esperas):>14.2f} {lat:>16.1f}")
    _, todas = api("GET", "/tareas")
    p(f"\ntareas acumuladas en memoria: {len(todas)}")


# ------------------------------------------------------------ medición 3B
def m3b(tamanos=(10, 50, 100, 150, 200, 400)):
    url = f"{LAT}/delay/1"
    p(f"MEDICIÓN 3B: UNA tarea 'descargar' con U URLs de {url} (~1s cada una)\n")
    p(f"{'U':>5} {'total(s)':>9} {'ok':>5} {'con error':>10}")
    for u in tamanos:
        t0 = time.perf_counter()
        _, t = crear("descargar", {"urls": [url] * u}, timeout=120)
        fin = esperar_fin([t["id"]], intervalo=0.1)[t["id"]]
        total = time.perf_counter() - t0
        res = (fin["resultado"] or {}).get("resultados", [])
        ok = sum(1 for r in res if "status" in r)
        p(f"{u:>5} {total:>9.2f} {ok:>5} {len(res) - ok:>10}   [{fin['estado']}]")


# ------------------------------------------------------------ ráfaga
def rafaga(n=1500, segundos=5):
    p(f"RÁFAGA: {n} tareas 'esperar' de {segundos}s enviadas lo más rápido posible")
    aceptadas, rechazadas = [], 0
    t0 = time.perf_counter()
    for _ in range(n):
        codigo, cuerpo = crear("esperar", {"segundos": segundos})
        if codigo == 202:
            aceptadas.append(cuerpo["id"])
        else:
            rechazadas += 1
    dt = time.perf_counter() - t0
    p(f"  aceptadas={len(aceptadas)}  rechazadas={rechazadas} (HTTP 429 cola llena)")
    p(f"  tiempo de envío: {dt:.2f}s ({n / dt:.0f} POST/s)")
    p(f"  latencia GET /tareas con {len(aceptadas)} tareas: {latencia_get() * 1000:.1f} ms")
    p("  cancelando todas para no esperar horas...")
    for i in aceptadas:
        api("DELETE", f"/tareas/{i}")
    _, est = api("GET", "/estadisticas")
    p(f"  estadísticas finales: {est['tareas_por_estado']}")


if __name__ == "__main__":
    comandos = {"m1": m1, "m3": m3, "m3b": m3b, "rafaga": rafaga}
    if len(sys.argv) != 2 or sys.argv[1] not in comandos:
        sys.exit(__doc__)
    comandos[sys.argv[1]]()
