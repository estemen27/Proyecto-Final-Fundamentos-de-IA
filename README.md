# Group Santi - Connect-4 Agent

## Resumen

Este branch contiene el agente final de Connect-4 de Group Santi. La versión actual usa minimax con poda alpha-beta y toma como variable principal de análisis la profundidad de búsqueda (`DEPTH`).

La idea es sencilla: mirar algunas jugadas hacia adelante, asumir que el rival responde bien y escoger la acción que mejor queda parada después de esa respuesta.

## Estructura

- `tournament/groups/Group Santi/policy.py`: agente `SantiPolicy`.
- `tournament/groups/Group Santi/entrega.ipynb`: estudio experimental y gráficas.
- `tournament/groups/Group Santi/results/`: resultados guardados por el notebook.

## Cómo correrlo

Desde la carpeta `tournament`:

```bash
python main.py
```

Eso ejecuta el torneo usando las políticas detectadas dentro de `groups`.

Para abrir el estudio:

```bash
jupyter notebook tournament/groups/Group\ Santi/entrega.ipynb
```

## Parámetros del agente

Los parámetros que realmente importan para la versión actual son:

- `DEPTH`: profundidad de búsqueda.
- `CENTER_WEIGHT`: preferencia por el centro.
- `TWO_IN_ROW_WEIGHT`: valor de ventanas con 2 fichas propias.
- `THREE_IN_ROW_WEIGHT`: valor de ventanas con 3 fichas propias.
- `OPP_THREE_PENALTY`: castigo por amenazas fuertes del rival.
- `WIN_SCORE` / `LOSS_SCORE`: prioridad de estados terminales.

## Qué estudia el notebook

El notebook de entrega cubre tres cosas que luego se mencionan en el PDF y en la sustentación:

- rendimiento contra jugador aleatorio por color,
- autodesempeño y comparación entre profundidades del mismo agente,
- costo computacional al aumentar la profundidad.

Además, deja guardadas las salidas del barrido para reutilizarlas en el informe.

## Entrega

La entrega está organizada para que quede clara en la revisión:

1. **Diseño del agente**  
   El agente es distinto a una política reactiva simple porque toma decisiones con búsqueda adversarial y poda alpha-beta.

2. **Análisis**  
   La variable numérica de estudio es `DEPTH`, y el notebook compara tanto contra aleatorio como entre versiones del mismo agente.

3. **Propuesta de mejora**  
   El costo crece rápido al subir profundidad, así que el estudio permite justificar una versión intermedia como mejor equilibrio entre calidad y tiempo.

4. **Presentación**  
   El notebook deja tablas y figuras para construir un PDF corto, directo y defendible.

## Resultados y figuras

Las figuras principales del notebook son:

- winrate contra aleatorio por profundidad,
- costo por jugada vs. profundidad,
- heatmap depth vs. depth,
- resumen visual de resultados completos por color.

Los resultados del barrido se guardan en JSON dentro de `tournament/groups/Group Santi/results/`.

## Ideas de mejora futura

- ajustar profundidad según la fase de la partida,
- usar mejor ordenamiento de jugadas,
- guardar estados repetidos para no evaluarlos dos veces,
- comparar una segunda versión del mismo agente con otra función de evaluación.