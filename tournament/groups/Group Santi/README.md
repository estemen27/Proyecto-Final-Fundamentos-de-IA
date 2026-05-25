# Group Santi - Connect-4 Agent

## Archivos de esta carpeta

- `policy.py`: implementacion del agente `SantiPolicy`.
- `entrega.ipynb`: notebook de validacion, graficas y analisis.

## Idea del agente

El agente usa minimax con poda alpha-beta.

Parametro clave:

- `DEPTH`: controla cuantas jugadas hacia adelante considera.

Heuristica actual:

- preferencia por centro,
- conteo de ventanas favorables de 2 y 3,
- penalizacion por amenazas de 3 del rival,
- prioridad de estados terminales (ganar/perder).

## Como correrlo

Desde la carpeta `tournament`:

```bash
python main.py
```

## Recomendacion para analisis

En `entrega.ipynb` hacer barrido de `DEPTH` (por ejemplo 2, 3, 4, 5), medir:

- winrate vs aleatorio por color,
- tiempo promedio por jugada,
- autodesempeno.

Con eso se puede sustentar la relacion costo-beneficio de aumentar profundidad.
