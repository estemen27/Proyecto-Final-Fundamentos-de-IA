# Connect-4 Minimax Agent (Group Santi)

## Resumen

Este proyecto implementa un agente de Connect-4 basado en minimax con poda alpha-beta.

La idea central es simple: en cada turno el agente mira varios pasos hacia adelante (lookahead) y asume que el rival siempre va a responder de la forma mas incomoda posible.

La variable numerica principal para el analisis es `DEPTH` (profundidad de busqueda).

## Que hace diferente a este agente

- Usa busqueda adversarial (minimax) en lugar de reaccionar solo al turno actual.
- Incluye poda alpha-beta para reducir ramas innecesarias.
- Prioriza explorar primero columnas centrales para podar mas temprano.
- Mantiene una heuristica compacta y legible (sin pesos exagerados).

## Donde esta el agente

- Archivo principal: `tournament/groups/Group Santi/policy.py`
- Clase: `SantiPolicy`

## Parametros importantes

En `policy.py`, los parametros mas relevantes son:

- `DEPTH`: cuantos plies mira hacia adelante.
- `CENTER_WEIGHT`: preferencia por control del centro.
- `TWO_IN_ROW_WEIGHT`: valor de ventanas favorables con 2 fichas.
- `THREE_IN_ROW_WEIGHT`: valor de ventanas favorables con 3 fichas.
- `OPP_THREE_PENALTY`: castigo por amenazas de 3 del rival.
- `WIN_SCORE` / `LOSS_SCORE`: prioridad de estados terminales.

## Ejecucion rapida

Desde la carpeta `tournament`:

```bash
python main.py
```

Esto ejecuta el torneo usando las politicas detectadas en `groups`.

## Validacion experimental (entrega.ipynb)

El notebook `tournament/groups/Group Santi/entrega.ipynb` debe cubrir:

- rendimiento vs jugador aleatorio por color (rojo y amarillo),
- autodesempeno (el agente contra si mismo),
- barrido de la variable numerica `DEPTH`,
- metricas de calidad (winrate) y costo (tiempo por jugada / tiempo total),
- graficas que soporten conclusiones.

## Como se alinea con la rubrica

1. Diseno de agente:
    El agente es explicable, implementado con una estrategia clara (minimax + poda), y su comportamiento depende de parametros concretos.

2. Analisis:
    Se propone evaluar en funcion de una variable numerica (`DEPTH`) y bajo diferentes oponentes (aleatorio y self-play), incluyendo separacion por color.

3. Propuesta de mejora:
    El analisis permite encontrar cuellos de botella de costo/beneficio (por ejemplo, mayor profundidad con mejora marginal de winrate) y justificar mejoras futuras.

4. Presentacion:
    Este README y el notebook estan pensados para que se pueda defender el diseno con evidencia reproducible.

## Ideas de mejora futura

- Ajustar dinamicamente la profundidad segun fase de partida.
- Agregar tabla de transposicion para reutilizar estados evaluados.
- Mejorar ordenamiento de jugadas con historial de cortes (move ordering adaptativo).
- Probar una segunda version del agente con la misma base y distinta funcion de evaluacion para comparar versiones en el informe.
