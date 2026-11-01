#!/bin/bash
# Medición 2: latencia de GET /tareas mientras corre un hash pesado.
# Uso: bash bench/medir_hash.sh [iteraciones]
# Correrlo con MODO_BLOQUEANTE=0 (executor) y luego con MODO_BLOQUEANTE=1.
IT=${1:-20000000}
ID=$(curl -s -X POST localhost:8000/tareas -H 'Content-Type: application/json' \
  -d "{\"tipo\":\"hashear\",\"parametros\":{\"texto\":\"hola\",\"iteraciones\":$IT},\"timeout\":120}" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
echo "Tarea lanzada: $ID"
for i in $(seq 1 10); do
  curl -s -o /dev/null -w "latencia GET /tareas: %{time_total}s\n" localhost:8000/tareas
  curl -s localhost:8000/tareas/$ID | python3 -c 'import sys,json; d=json.load(sys.stdin); print("   estado:", d["estado"])'
  sleep 0.5
done