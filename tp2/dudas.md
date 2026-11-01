# Plataforma de tareas distribuidas (TP2)

Servicio HTTP al que se le encargan trabajos, que los ejecuta de forma concurrente
con un pool de workers (corrutinas + `asyncio.Queue`) y permite consultar su estado
y resultado. Tres tipos de tarea: `descargar` (I/O-bound), `hashear` (CPU-bound) y
`esperar` (I/O simulado, para probar cancelación y timeouts).

## 1. Uso

```bash
docker compose up --build        # API en http://localhost:8000
```

Levanta dos contenedores: `api` (el servicio) y `latencia` (servidor local de
latencia fija, usado solo en las mediciones). Documentación interactiva en
`http://localhost:8000/docs`.

### Ejemplos con curl

```bash
# Encolar una tarea (responde 202 al instante con id y estado "pendiente")
curl -X POST localhost:8000/tareas -H 'Content-Type: application/json' \
  -d '{"tipo":"esperar","parametros":{"segundos":30}}'

curl -X POST localhost:8000/tareas -H 'Content-Type: application/json' \
  -d '{"tipo":"hashear","parametros":{"texto":"hola","iteraciones":20000000}}'

curl -X POST localhost:8000/tareas -H 'Content-Type: application/json' \
  -d '{"tipo":"descargar","parametros":{"urls":["https://example.com","https://www.python.org"]},"timeout":20}'

curl localhost:8000/tareas                      # listar todas
curl "localhost:8000/tareas?estado=ejecutando"  # filtrar por estado
curl localhost:8000/tareas/<id>                 # estado y resultado
curl -X DELETE localhost:8000/tareas/<id>       # cancelar (pendiente o en curso)
curl localhost:8000/estadisticas                # totales, tiempos, workers ocupados
```

Estados: `pendiente`, `ejecutando`, `completada`, `fallida`, `cancelada`.
Códigos de error: 404 (id inexistente), 409 (cancelar una tarea ya terminada),
422 (parámetros inválidos), 429 (cola llena), 503 (servicio apagándose).

### Configuración (variables de entorno en `docker-compose.yml`)

| Variable | Defecto | Significado |
|---|---|---|
| `NUM_WORKERS` | 4 | Workers (corrutinas) que consumen la cola |
| `TAMANO_COLA` | 1000 | `maxsize` de la `asyncio.Queue` |
| `TIMEOUT_DEFECTO` | 60 | Timeout por tarea (s), si el POST no indica `timeout` |
| `LIMITE_APAGADO` | 10 | Espera máxima a tareas en curso al apagar (s) |
| `MAX_PROCESOS` | nº de CPUs | Procesos del `ProcessPoolExecutor` |
| `MODO_BLOQUEANTE` | 0 | `1` ejecuta el hash dentro del event loop (solo para la medición 2) |

## 2. Arquitectura

```
 Cliente HTTP
      |
      v
 +--------------------+  put_nowait   +------------------------+
 | API (FastAPI)      | ------------> | asyncio.Queue          |
 | POST   /tareas     |               | (maxsize = 1000)       |
 | GET    /tareas[/id]|               +-----------+------------+
 | DELETE /tareas/id  |                           | await get()
 | GET /estadisticas  |                           v
 +---------^----------+               +------------------------+
           |  lee estado/resultado    | Pool de N workers      |
           |  (dict en memoria)       | (N corrutinas)         |
           +--------------------------+  descargar -> httpx    |
                                      |  esperar   -> asyncio.sleep
                                      |  hashear   -> ProcessPoolExecutor
                                      +------------------------+
```

Flujo de una tarea:

1. `POST /tareas` valida los parámetros, crea la `Tarea` (estado `pendiente`) y hace
   `put_nowait` en la cola. Responde 202 sin esperar la ejecución.
2. Un worker libre saca la tarea con `await cola.get()`, la pasa a `ejecutando` y la
   corre como un `asyncio.Task` propio, envuelto en `asyncio.wait_for` (timeout).
3. Al terminar queda `completada` (con resultado), `fallida` (con el motivo) o
   `cancelada`.
4. `GET /tareas/{id}` lee el estado del diccionario en memoria.

Archivos: `app/main.py` (rutas y apagado), `app/pool.py` (cola, workers,
cancelación), `app/ejecutores.py` (los tres tipos de tarea), `app/modelos.py`,
`app/persistencia.py`, `app/config.py`.

## 3. Decisiones de diseño

### ¿Por qué `asyncio.Queue` y no `queue.Queue`?
`queue.Queue.get()` bloquea el *hilo* que lo llama. En una corrutina eso congela el
event loop entero. `asyncio.Queue.get()` es un `await`: suspende solo a la corrutina
que espera y el loop sigue atendiendo a las demás. Además `asyncio.Queue` no es
thread-safe y acá no hace falta: todo el código del pool corre en un único hilo.
Se usa `maxsize` para tener contrapresión (HTTP 429) y `join()`/`task_done()` para
esperar a que la cola se vacíe en el apagado.

### ¿Cómo evito que una tarea CPU-bound congele la API?
`hashear` se ejecuta con `loop.run_in_executor(ProcessPoolExecutor, ...)`. Mientras
un proceso hijo calcula, el event loop solo hace `await` del resultado y sigue
atendiendo requests. Elegí **procesos y no threads** porque el hash iterado trabaja
sobre 32 bytes por vez, y `hashlib` solo libera el GIL con entradas grandes
(más de ~2 KB): con threads el GIL seguiría tomado casi todo el tiempo y degradaría
el loop. *(Esta última parte es razonamiento a partir de cómo funciona CPython; no
medí la variante con threads.)* La medición 2 muestra el efecto con números.

### ¿Cómo implementé la cancelación y qué pasa con los recursos a medio usar?
- **Tarea pendiente:** `asyncio.Queue` no permite sacar elementos del medio, así que
  se marca como `cancelada` y el worker la salta cuando la saca de la cola.
- **Tarea en ejecución:** cada tarea corre en su propio `asyncio.Task`; el `DELETE`
  llama a `task.cancel()` sobre *ese* task, no sobre el worker, que sigue vivo y
  toma la próxima. El `DELETE` espera a que la limpieza termine antes de responder.
- **`descargar`:** el `AsyncClient` está en un `async with`; al llegar el
  `CancelledError` las conexiones abiertas se cierran, y `gather` cancela las
  descargas hijas. No quedan corrutinas huérfanas.
- **`hashear`:** un `Future` de `ProcessPoolExecutor` que ya empezó **no se puede
  cancelar**. Por eso el hash se hace en lotes de 200.000 iteraciones y el proceso
  hijo consulta un `multiprocessing.Event` entre lotes. Al cancelar o vencer el
  timeout, el bloque `finally` activa el evento y el hijo corta en el siguiente
  lote (a la velocidad medida, ~1,6 M iteraciones/s, un lote dura ~0,13 s).
- **Timeout:** `asyncio.wait_for` cancela la tarea al vencer; el estado pasa a
  `fallida` con `timeout tras Xs`. El tiempo cuenta desde que la tarea empieza a
  ejecutarse, no desde que se encola.

### ¿Qué pasa si un worker lanza una excepción no capturada?
Hay dos redes de seguridad. `_correr` captura `Exception` por tarea y la deja
`fallida` con `TipoDeError: mensaje`. Y el bucle del worker tiene su propio
`try/except Exception` que registra el error y sigue. `CancelledError` se distingue
y se re-lanza siempre (hereda de `BaseException`, así que no la atrapa el
`except Exception`). Un worker nunca muere por culpa de una tarea.

### Apagado ordenado (SIGTERM / SIGINT)
Uvicorn atiende ambas señales y dispara la parte posterior al `yield` del `lifespan`
de FastAPI. Ahí: se marca el pool como cerrado (el POST pasa a devolver 503), se
espera hasta `LIMITE_APAGADO` segundos a que la cola se vacíe, se cancela lo que
quede, y se vuelca el estado a `estado_<timestamp>.json`. Al arrancar se loguea el
último volcado encontrado. En el `Dockerfile` el `CMD` va en formato exec para que
Python sea PID 1 y reciba SIGTERM; `stop_grace_period` (20 s) es mayor que
`LIMITE_APAGADO` (10 s).

### Cliente HTTP: `httpx` (modo async)
API cercana a `requests`, soporta `AsyncClient` como context manager (cierra
conexiones aunque se cancele) y tiene timeouts y límites configurables.
COMPLETAR: comparar brevemente con `aiohttp` según lo que hayas leído.

## 4. Mediciones

Entorno: COMPLETAR (CPU, RAM, SO, versión de Docker). El contenedor vio 12 CPUs.
Servidor de latencia local (`latencia/servidor.py`, 1 s por respuesta) para que los
números no dependan de internet. Scripts en `bench/`.

### Medición 1: concurrencia I/O (`python3 bench/bench.py m1`)
20 descargas de una URL con 1 s de latencia, mediana de 3 repeticiones:

| Variante | Tiempo |
|---|---|
| A) 20 secuenciales (una tarea por URL, esperando cada una) | 20,50 s |
| B) 20 concurrentes (una tarea con 20 URLs, `asyncio.gather`) | 1,05 s |
| C) 20 tareas de 1 URL repartidas por el pool de 4 workers | 5,21 s |

**Speedup B vs A: 19,6x.** La secuencial paga la suma de las esperas; la concurrente
paga aproximadamente la más lenta, porque mientras una corrutina espera la red el
loop atiende a las otras. En C el límite lo pone el pool: 20 tareas / 4 workers =
5 tandas de ~1 s. Las diferencias con el ideal (20,50 vs 20 s; 5,21 vs 5 s) son el
overhead por tarea (POST, cola, polling de 20 ms del script).

### Medición 2: event loop bloqueado (`bash bench/medir_hash.sh`)
Hash de 20.000.000 de iteraciones de SHA-256. Se lanza la tarea y se mide, 10
veces, cuánto tarda `GET /tareas`.

| Modo | Latencia de `GET /tareas` durante el hash |
|---|---|
| Con `run_in_executor` (procesos) | 2,6 a 2,9 ms (la primera, 5,3 ms); la tarea seguía `ejecutando` en las 10 mediciones |
| Bloqueante (`MODO_BLOQUEANTE=1`) | **12,68 s** la primera; después 2,3 a 3,6 ms |

La diferencia es de unas 4.500 veces. En modo bloqueante el hash corre dentro de una
corrutina: el loop no ejecuta nada más hasta que termina, y el GET quedó esperando
los ~12,7 s del cálculo. Con el executor el cálculo ocurre en otro proceso (otro
intérprete, otro GIL) y el loop queda libre.
Nota: en modo bloqueante el timeout tampoco puede interrumpir el hash, porque el
loop no tiene oportunidad de ejecutarlo.

### Medición 3: techo del pool

**3A. Tareas concurrentes (`bench.py m3`)**: M tareas `esperar` de 0,5 s, 4 workers.

| M | Total (s) | Ideal (s) | Espera media en cola (s) | Espera máx (s) |
|---|---|---|---|---|
| 4 | 0,64 | 0,50 | 0,00 | 0,00 |
| 8 | 1,08 | 1,00 | 0,25 | 0,50 |
| 16 | 2,18 | 2,00 | 0,75 | 1,51 |
| 32 | 4,05 | 4,00 | 1,74 | 3,49 |
| 64 | 8,08 | 8,00 | 3,73 | 7,47 |
| 128 | 16,18 | 16,00 | 7,72 | 15,46 |
| 256 | 32,29 | 32,00 | 15,69 | 31,37 |
| 512 | 64,21 | 64,00 | 31,57 | 63,19 |

El pool no se degrada: satura. El throughput es constante (4 workers / 0,5 s =
8 tareas/s) y el tiempo total sigue el ideal. Lo que crece linealmente es la espera
en cola: con 512 tareas la última espera 63 s antes de empezar. El techo es
`NUM_WORKERS / duración de la tarea`; se sube con más workers.

**3B. Conexiones dentro de una tarea (`bench.py m3b`)**: una tarea `descargar` con U
URLs de 1 s.

| U | Total (s) | Errores |
|---|---|---|
| 10 | 1,08 | 0 |
| 50 | 1,20 | 0 |
| 100 | 1,21 | 0 |
| 150 | 2,35 | 0 |
| 200 | 2,60 | 0 |
| 400 | 6,78 | 0 |

Hasta 100 URLs el tiempo es el de una sola descarga; desde 150 se escalona. Coincide
con el límite por defecto de `httpx` de 100 conexiones simultáneas por cliente
(las demás esperan turno). Con 400 URLs esperaba ~4,5 s y tardó 6,78 s: **no
identifiqué la causa**. Hipótesis sin comprobar: el servidor de latencia cierra cada
conexión (`Connection: close`) y cada tanda paga abrir sockets nuevos.

**Ráfaga (`bench.py rafaga`)**: 1.500 tareas de golpe. Se aceptaron 1.004 y se
rechazaron 496 con HTTP 429 (1.000 de la cola + 4 que los workers sacaron enseguida).
Al cancelarlas todas: `pendiente 0`, `ejecutando 0`, `cancelada 1004`. Lo primero que
se agota es la cola, y falla de forma controlada.

**Hallazgo: `GET /tareas` crece con la cantidad de tareas guardadas.**

| Tareas en memoria | Latencia de `GET /tareas` |
|---|---|
| 135 | 9,4 ms |
| 375 | 15,8 ms |
| 631 | 23,4 ms |
| 1.143 | 35,4 ms |
| 2.153 | 75,2 ms |

El costo es lineal (~30 a 35 µs por tarea). `listar_tareas` serializa todo el
diccionario de forma síncrona y, mientras lo hace, el event loop no atiende a nadie.
Es el lugar donde mi código puede bloquear el loop (ver limitaciones).

## 5. Conceptos del curso aplicados

COMPLETAR con los nombres/números reales de tus clases. Ideas de relaciones:

- **Productor-consumidor:** la API produce (`put_nowait`) y el pool de workers
  consume (`await get()`) de una `asyncio.Queue` compartida. Es el patrón de la
  clase 11, pero con corrutinas en vez de threads: acá no hace falta lock porque el
  event loop no interrumpe entre `await`s. `self.ocupados += 1` es seguro porque no
  hay ningún `await` entre leer y escribir.
- **GIL y CPU-bound:** COMPLETAR (clase de threads/GIL) ↔ `ProcessPoolExecutor`.
- **Procesos y comunicación entre procesos:** COMPLETAR ↔ `multiprocessing.Manager().Event()`
  para avisar al hijo que corte.
- **Señales:** COMPLETAR ↔ SIGTERM/SIGINT y apagado ordenado.
- **Docker/PID 1:** COMPLETAR ↔ `CMD` en formato exec y `stop_grace_period`.

## 6. Limitaciones conocidas

- `GET /tareas` serializa todo el diccionario de forma síncrona: con muchas tareas
  bloquea el loop (medido arriba). Falta paginación.
- Las tareas terminadas nunca se borran: el diccionario crece sin tope.
- Una tarea pendiente cancelada sigue ocupando un lugar de la cola hasta que un
  worker la saque.
- Cancelación de `hashear` con granularidad de lote (~0,13 s): el proceso hijo sigue
  calculando hasta el final del lote actual.
- Cada `Event` del `Manager` usa IPC; `cancelar.set()` se llama de forma síncrona
  (microsegundos de bloqueo del loop).
- El volcado a JSON se reporta al arrancar pero no se vuelve a cargar.
- Si el proceso muere con SIGKILL no hay volcado.
- Cada tarea `descargar` crea su propio `AsyncClient`: el límite de 100 conexiones es
  por tarea, no global.
- Sin autenticación ni límite de tamaño en los parámetros (p. ej. `iteraciones`).
- El timeout cuenta desde el inicio de la ejecución, no desde el encolado.

## 7. Lo que aprendí

COMPLETAR (2 a 3 párrafos, en primera persona). Ideas para arrancar: qué fue lo que
más te costó (¿la cancelación del hash en un proceso hijo?); qué te sorprendió de las
mediciones (¿los 12,7 s del GET bloqueado? ¿que el pool no se degrada sino que
satura?); qué harías distinto; qué parte pudiste explicar sin mirar el código.