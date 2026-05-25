# Agente Connect-4 — FVMC con Reward Shaping
**Esteban Bernal Cortés** · Fundamentos de Inteligencia Artificial 2026.1

---

## Descripción

El agente juega Connect-4 mediante simulaciones de Monte Carlo. Antes de cada jugada corre `n_trials` trayectorias completas desde el estado actual, actualiza una tabla de valores Q con el resultado de cada trayectoria, y elige la columna con el valor esperado más alto. No hay árbol de búsqueda: la estructura central es una tabla Q plana indexada por `(tablero_serializado, columna)`.

La diferencia conceptual respecto al agente MCTS del grupo es que ese mantiene un árbol explícito con UCB para guiar la expansión, mientras que este agente usa *exploring starts* (primera acción aleatoria forzada en cada trial) para garantizar cobertura sin necesidad de árbol. El algoritmo corresponde al *Trial-Based Online Policy Improvement* visto en clase, el paso previo a MCTS.

El repositorio tiene dos versiones:

- **V1** — FVMC sin reward shaping (`shaping_weight=0`). Solo aprende del resultado final de la partida.
- **V2** — FVMC con reward shaping (`shaping_weight=0.1`). Añade un bonus basado en amenazas del tablero al final de cada simulación, lo que densifica la señal de aprendizaje.

Código final: [`branch esteban/MCTS-agent`](https://github.com/estemen27/Proyecto-Final-Fundamentos-de-IA/tree/esteban/MCTS-agent)

---

## Uso

```python
from policy import FVMCPolicy

# Versión V2 (recomendada)
agente = FVMCPolicy(n_trials=500, shaping_weight=0.1)

# El torneo llama a act() pasando el tablero 6×7
columna = agente.act(tablero)   # tablero: np.ndarray con valores {-1, 0, 1}
```

El agente infiere automáticamente de quién es el turno contando las fichas en el tablero, por lo que no necesita información adicional. La tabla Q persiste entre jugadas y entre partidas: el agente acumula conocimiento a lo largo del torneo.

### Parámetros

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `n_trials` | `500` | Simulaciones por jugada. Más trials = decisiones más precisas, más lento. |
| `shaping_weight` | `0.1` | Peso del reward shaping. `0` desactiva el shaping (V1). |
| `max_rollout` | `50` | Longitud máxima de cada simulación. |

---

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `policy.py` | Código del agente, listo para importar en el torneo |
| `entrega.ipynb` | Experimentos de validación y análisis del agente |
