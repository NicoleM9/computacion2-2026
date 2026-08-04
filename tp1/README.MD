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
