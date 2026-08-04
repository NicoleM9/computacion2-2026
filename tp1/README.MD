# 🖥️ Monitor de Procesos y Sistema en Tiempo Real (TP1 - Computación II)

## 📌 Descripción General

Este proyecto es un monitor interactivo de procesos y métricas del sistema operativo Linux que funciona directamente desde la terminal (TUI). Su objetivo principal es ofrecer una visión clara, estructurada y en tiempo real del estado de la máquina y de cada uno de sus procesos en ejecución, permitiendo analizar aspectos clave como el consumo de memoria, hilos, descriptores de archivos, señales y prioridades del planificador.

Para utilizarlo, basta con ejecutar el contenedor Docker e interactuar con el teclado dentro de la terminal. El usuario puede alternar fácilmente entre 7 vistas especializadas mediante las teclas `1` a `7` (o sus letras correspondientes), navegar por la lista de procesos con las flechas del teclado, fijar un proceso específico con la tecla `Enter` para profundizar en sus métricas, aplicar filtros en tiempo real por comando (`/`) o usuario (`u`), y cambiar el criterio de ordenamiento de la lista presionando la tecla `c` (alternando entre uso de CPU%, memoria RSS y PID). Además, permite ajustar la frecuencia de refresco de cada vista en tiempo real mediante las teclas `+` y `-`.

---

## 🏗️ Diagrama de Arquitectura

El sistema se divide en procesos independientes que ejecutan tareas específicas de recolección y renderizado, comunicándose a través de memoria compartida y un mecanismo seguro de señales.

```mermaid
graph TD
    %% Estilos de Nodos
    classDef mainNode fill:#1f2937,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef subNode fill:#111827,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef ipcNode fill:#374151,stroke:#f59e0b,stroke-width:2px,color:#fff;

    MAIN["PROCESO PRINCIPAL (main)<br/>• Inicializa memoria compartida y Self-Pipe<br/>• Captura señales (SIGINT, SIGHUP, SIGUSR1)"]:::mainNode
    WORKER["SUBPROCESO RECOLECTOR (worker)<br/>• Lee /proc (stat, status, fd)<br/>• Calcula CPU% por diferencia<br/>• Respeta timers de cada vista"]:::subNode
    UI["SUBPROCESO DISPLAY / TUI (ui)<br/>• Renderiza la pantalla (curses)<br/>• Captura entrada de teclado<br/>• Permite ordenar, filtrar y pinar"]:::subNode
    
    MEM["MEMORIA COMPARTIDA (multiprocessing)<br/>• snapshot_dict (Manager.dict)<br/>• intervals_dict (Value)<br/>• running_flag (Value)"]:::ipcNode

    MAIN -->|Fork / Spawns| WORKER
    MAIN -->|Fork / Spawns| UI
    WORKER -->|Escribe métricas| MEM
    UI -->|Lee métricas| MEM
    UI -->|Modifica intervalos| MEM

# Decisiones de Diseño Argumentadas
---
## Selección de Mecanismos de IPC
---
Para la transferencia de métricas entre el proceso recolector y la interfaz gráfica utilicé un diccionario compartido gestionado por multiprocessing.Manager. Elegí este mecanismo porque la estructura de datos que viaja desde /proc hacia la TUI es compleja (diccionarios anidados con listas de procesos, métricas de memoria y textos de estado) y cambia dinámicamente según la cantidad de PIDs activos. Intentar empaquetar esta estructura variable en bloques rígidos de memoria compartida pura hubiera requerido una sobrecarga de serialización innecesaria.

Para los intervalos de refresco y el estado de parada del programa utilicé multiprocessing.Value de tipo flotante y entero. En este caso, al tratarse de valores numéricos atómicos y simples, Value es mucho más rápido y ligero que un Manager, garantizando un acceso directo en memoria sin pasar por un proceso servidor intermediario.
---
## Manejo de Race Conditions
---
Las condiciones de carrera se evitaron asegurando que los roles de escritura y lectura estén perfectamente definidos. El subproceso recolector es el único productor que escribe las métricas en el diccionario compartido snapshot_dict, mientras que el subproceso de la TUI actúa únicamente como un consumidor que lee la información para dibujarla en pantalla. Para evitar incoherencias visuales cuando el recolector actualiza una vista mientras la TUI la está dibujando, el recolector reemplaza la clave de la vista entera en una sola operación atómica en lugar de modificar elemento por elemento.

En cuanto a las señales externas, para evitar carreras entre el hilo de ejecución normal y las interrupciones del kernel, apliqué el patrón Self-Pipe Trick. El manejador de la señal se limita a escribir un único byte en un pipe interno de forma asíncrona y segura (async-signal-safe), y es el bucle principal de la TUI el que lee dicho byte de forma sincrónica para ejecutar la acción correspondiente (recargar configuración, volcar JSON o cerrar).
---
## Justificación de Intervalos por Defecto
---
Los tiempos de refresco asignados por defecto a cada vista responden al nivel de volatilidad de los datos que muestran:

    -Resumen (0.5s) y Threads (0.5s): Tienen la frecuencia más alta porque el uso de CPU y el estado de los hilos cambian constantemente, requiriendo una respuesta visual inmediata.

    -Memoria (1.0s) y Sistema Global (1.0s): Cambian a un ritmo moderado en el uso general del equipo.

    -File Descriptors (2.0s): Se estableció en 2 segundos para no saturar las operaciones de entrada/salida (I/O) del disco al inspeccionar la carpeta /proc/[pid]/fd de cientos de procesos en cada ciclo.

   -Señales (5.0s) y Scheduling (5.0s): Tienen los intervalos más largos debido a que las máscaras de señales y las prioridades (nice) de un proceso rara vez cambian durante su ejecución habitual.
---
## Conceptos del Curso Aplicados
---
-Estructura Virtual /proc: Acceso directo a los archivos del sistema operativo sin librerías de alto nivel como psutil. En la vista de Resumen y Scheduling se interpreta /proc/[pid]/stat omitiendo el nombre del ejecutable para evitar errores cuando el comando contiene espacios.

-Procesos Zombies y Ciclo de Vida: En la vista de Sistema Global realizo un conteo de los procesos según su estado (R, S, D, Z, T). Un proceso en estado Z (Zombie) representa el concepto visto en clase sobre procesos que finalizaron su ejecución pero cuyo padre aún no ha ejecutado la llamada al sistema wait().

-Handlers Async-Signal-Safe: Implementación de la captura de señales del kernel (SIGINT, SIGHUP, SIGUSR1, SIGUSR2) utilizando funciones seguras. Al canalizar las señales mediante el patrón Self-Pipe Trick, se evita la corrupción del estado gráfico administrado por curses.

-Cálculo de CPU% por Diferencial: Dado que /proc/[pid]/stat solo guarda el tiempo acumulado desde la creación del proceso (utime + stime), implementé un cálculo diferencial midiendo el incremento de ticks de reloj consumidos entre dos muestras consecutivas sobre el tiempo transcurrido, aplicando la frecuencia del reloj del kernel (SC_CLK_TCK).
---
##Limitaciones Conocidas
---
-Permisos sobre File Descriptors: Al ejecutar el monitor con un usuario no privilegiado o dentro del contenedor sin permisos de superusuario, la lectura de la carpeta /proc/[pid]/fd de procesos de otros usuarios (root) devolverá listas vacías por restricciones de seguridad del sistema.

-Muestreo Inicial de CPU%: Dado que el porcentaje de CPU se calcula por diferencia respecto a una toma previa, durante los primeros dos segundos de ejecución todos los procesos reportarán 0.0% hasta que se construya el primer historial de lecturas.

-Nombres de comandos truncados: El sistema de archivos /proc limita la longitud del nombre del ejecutable guardado en /proc/[pid]/stat a 16 caracteres, por lo que nombres de comandos extensos aparecerán cortados en la columna COMM.
---
#Cómo Correr y Testear
---
# 1. Ejecución
---
## Construir la imagen de Docker y levantar el contenedor:

docker compose up -d --build

## Conectarse a la terminal interactiva:

docker attach monitor_proc_tui
---
# 2. Controles Principales
---
1 a 7 (o r, m, f, t, s, p, g): Cambiar de vista.

↑ / ↓: Seleccionar un proceso de la lista.

 Enter: Fijar (Pin) el PID seleccionado para mantenerlo en el panel inferior.

 c: Alternar ordenamiento (CPU% -> RSS -> PID).

 / / u: Filtrar por comando o UID.

 + / -: Incrementar o disminuir el tiempo de refresco de la vista activa.

 q: Salir de forma limpia.
---
# 3. Pruebas de Señales
---
Desde una segunda pestaña de terminal:

# Recargar configuración desde config.json
docker kill --signal=SIGHUP monitor_proc_tui

# Generar snapshot JSON
docker kill --signal=SIGUSR1 monitor_proc_tui

# Cierre seguro
docker kill --signal=SIGINT monitor_proc_tui

# Decisiones sobre la TUI

Elegí la librería estándar curses para la construcción de la interfaz por dos razones principales: al ser un módulo nativo de Python, evita dependencias externas garantizando la máxima portabilidad; además, ofrece un control exacto sobre cada celda de la terminal, lo que permitió diseñar una pantalla dividida en dos secciones (Split Layout).

El layout ubica en la mitad superior la tabla general de procesos (que se mantiene fija para no perder el contexto del sistema) y en la mitad inferior el panel de detalle dinámico que muestra la información extendida de la vista o del PID fijado.
---
# Lo que Aprendí
---
Desarrollar este monitor me permitió comprender la complejidad que hay detrás de las herramientas de administración del sistema como top. Entender que las métricas surgen de la lectura e interpretación de archivos de texto en /proc mantenidos por el kernel de Linux reforzó de forma práctica el concepto de que en Unix "todo es un archivo".

A nivel de arquitectura de software, el mayor aprendizaje estuvo en la gestión de la concurrencia y la prevención de bloqueos. Diseñar la comunicación entre subprocesos con multiprocessing y dominar el patrón Self-Pipe Trick para integrar señales asíncronas dentro de un bucle de renderizado interactivo me dio una visión clara sobre cómo construir aplicaciones robustas a bajo nivel.
