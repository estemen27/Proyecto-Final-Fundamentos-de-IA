# Agente Connect-4: FVMC con Reward Shaping y Single Shared Q
### Fundamentos de Inteligencia Artificial 2026.1
**Autor:** Esteban Bernal Cortés

---

## Descripción del agente

Trial-Based Online Policy Improvement (Slides 13, pg 11–14) **sin árbol de
búsqueda**. Combina los componentes vistos en clase:

- **First-Visit Monte Carlo (FVMC)** — Slides 11, pg 14
- **Exploring Starts** — Slides 11, pg 22
- **Reward Shaping** — Slides 11, pg 26
- **Single Shared Q** — Slides 12, pg 16
- **Sign-flip × (−1) por turno** — Slides 12, pg 17
- **Default policy uniforme** — Slides 13

**Factor diferencial frente al MCTS del grupo.** El compañero usa MCTS con tabla
de transposición. MCTS mantiene un árbol explícito y distingue tree policy
(UCB) de default policy. Este agente **no mantiene árbol**: es exactamente el
algoritmo previo a MCTS de las slides 13. La diferencia conceptual:

|                   | MCTS del compañero      | Este agente FVMC                  |
|-------------------|-------------------------|-----------------------------------|
| Estructura        | Árbol + hashing         | Q-table plana (estado, acción)    |
| Tree policy       | UCB                     | —                                 |
| Update            | Por nodos del árbol     | FVMC sobre la trayectoria         |
| Recompensa        | Sólo terminal ±1        | Terminal + Reward Shaping         |
| Inicio del trial  | Estado raíz             | Exploring Starts (acción aleatoria) |

---

## Uso

```python
from policy import FVMCPolicy

agente = FVMCPolicy(n_trials=500, shaping_weight=0.1)
accion = agente.act(tablero)
```

**Parámetros:**
- `n_trials` (int, default=500) — presupuesto de simulación por jugada.
- `shaping_weight` (float, default=0.1) — peso del reward shaping; activa o desactiva la mejora respecto a la versión vainilla.
- `max_rollout` (int, default=50) — máximo de pasos por simulación.

---

## Archivos

| Archivo         | Descripción                                                    |
|-----------------|----------------------------------------------------------------|
| `policy.py`     | Código completo del agente (único archivo necesario)           |
| `entrega.ipynb` | Notebook con experimentos y gráficas de validación             |
| `informe.tex`   | Informe en LaTeX (compilar a PDF para entrega en Teams)        |
| `.gitignore`    | Ignora `.idea/`, `CLAUDE.md`, informes y figuras generadas      |

---

## Explicación en 3 líneas

1. **Simulo muchas trayectorias** desde la posición actual; cada una empieza con una acción aleatoria (Exploring Starts) y continúa con jugadas uniformemente aleatorias.
2. **Calculo la utility** de cada trayectoria: el resultado del juego $\pm 1$ más un bonus por amenazas creadas en el tablero (Reward Shaping).
3. **Actualizo $\hat q(s,a)$ con FVMC** para cada par estado–acción de la trayectoria, multiplicando la utility por $\pm 1$ según a quién le tocaba jugar (Single Shared Q). Al final, elijo la columna con mayor $\hat q$.

---

## Fundamento teórico

| Concepto                              | Origen          | Rol en el agente                            |
|---------------------------------------|-----------------|---------------------------------------------|
| Alternating Markov Game               | Slides 12       | Modelo formal del juego                     |
| First-Visit Monte Carlo (FVMC)        | Slides 11, pg 14 | Update de $\hat q$ por trayectoria          |
| Exploring Starts                      | Slides 11, pg 22 | Primera acción aleatoria en cada trial      |
| Reward Shaping                        | Slides 11, pg 26 | Recompensas sintéticas por amenazas         |
| Single Shared Q                       | Slides 12, pg 16 | Una sola q-table para ambos jugadores       |
| Sign-flip × (−1) por turno            | Slides 12, pg 17 | Propaga utility en juego zero-sum           |
| Trial-Based Online Policy Improvement | Slides 13, pg 11–14 | Marco general (precede a MCTS)         |
