#!/bin/bash
# Prueba del apagado ordenado con una tarea en curso.
# Correr desde cualquier carpeta, con el servicio levantado (docker compose up).
cd "$(dirname "$0")/.."
curl -s -X POST localhost:8000/tareas -H 'Content-Type: application/json' \
  -d '{"tipo":"esperar","parametros":{"segundos":60}}' \
  || { echo "La API no responde: levantala con 'docker compose up'"; exit 1; }
echo
sleep 1
echo "Apagando con 'docker compose stop'..."
INICIO=$(date +%s)
docker compose stop
echo "stop tardó $(( $(date +%s) - INICIO )) s"
ULTIMO=$(ls -t volcados | head -1)
echo "Último volcado: volcados/$ULTIMO"
python3 - "volcados/$ULTIMO" <<'PY'
import collections, json, sys
tareas = json.load(open(sys.argv[1]))["tareas"]
print(len(tareas), "tareas en el volcado")
cuenta = collections.Counter((t["estado"], t["error"]) for t in tareas)
for (estado, error), n in cuenta.items():
    print(f"  {n:5d}  {estado:11s} {error or ''}")
PY