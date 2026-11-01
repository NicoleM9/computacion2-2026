#!/bin/bash
# Verifica que cancelar un 'hashear' en curso libera la CPU del contenedor.
# Correr con el servicio levantado (docker compose up).
cd "$(dirname "$0")/.."
RESP=$(curl -s -X POST localhost:8000/tareas -H 'Content-Type: application/json' \
  -d '{"tipo":"hashear","parametros":{"texto":"hola","iteraciones":2000000000},"timeout":300}')
ID=$(echo "$RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])' 2>/dev/null)
[ -z "$ID" ] && { echo "La API no responde: levantala con 'docker compose up'"; exit 1; }
CONT=$(docker compose ps -q api)
echo "Tarea lanzada: $ID"
sleep 3
echo "CPU con el hash corriendo:"
docker stats --no-stream --format "  {{.Name}} CPU: {{.CPUPerc}}" "$CONT"
echo "Cancelando..."
curl -s -X DELETE localhost:8000/tareas/$ID | python3 -c 'import sys,json; d=json.load(sys.stdin); print("  estado:", d["estado"], "|", d["error"])'
sleep 2
echo "CPU 2 s después de cancelar:"
docker stats --no-stream --format "  {{.Name}} CPU: {{.CPUPerc}}" "$CONT"