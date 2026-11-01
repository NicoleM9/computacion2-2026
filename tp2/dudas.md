# Dudas

1. **Servicio concreto o plataforma genérica.** Entendí que lo evaluado es la
   plataforma con los tres tipos de tarea obligatorios (`descargar`, `hashear`,
   `esperar`) y no un servicio de dominio específico encima. ¿Es correcto?

2. **Cancelación de CPU-bound.** Un `Future` de `ProcessPoolExecutor` ya iniciado no
   se puede cancelar. Resolví con lotes y un `multiprocessing.Event`, lo que deja al
   proceso hijo corriendo hasta el final del lote (~0,13 s). ¿Es aceptable, o se
   espera matar el proceso y recrear el pool?

3. **Medición 3B (400 URLs).** Con 400 URLs en una tarea esperaba ~4,5 s (4 tandas
   por el límite de 100 conexiones de `httpx`) y medí 6,78 s. No logré explicar la
   diferencia; mi hipótesis es el costo de abrir conexiones nuevas, pero no la
   comprobé. ¿Hay algo que deba medir para confirmarlo?

4. **`GET /tareas` y el event loop.** Mido que la latencia crece linealmente con las
   tareas guardadas (75 ms con ~2.150). ¿Alcanza con documentarlo como limitación,
   o conviene implementar paginación y retención de tareas terminadas?