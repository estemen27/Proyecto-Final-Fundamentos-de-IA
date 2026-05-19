# Agente MCTS — Connect-4
### Fundamentos de Inteligencia Artificial · Universidad de La Sabana · 2026.1
**Autor:** Esteban Bernal Cortés · Grupo Esteban

---

## Descripción del agente

Este agente juega Connect-4 usando **Monte-Carlo Tree Search (MCTS)** con exploración por **UCB** y evaluación de política mediante **First-Visit Monte Carlo (FVMC)**. Está diseñado para integrarse directamente con el sistema de torneo provisto por el curso, implementando de forma fiel los conceptos de los tres módulos de decisiones secuenciales bajo incertidumbre.

### Fundamento teórico (todo el diseño está en el curso)

| Concepto | Origen | Rol en el agente |
|---|---|---|
| FVMC — `q̂(s,a) += (U − q̂) / N` | Slides 11 | Actualiza valores en backpropagation |
| Alternating Markov Game | Slides 12 | Modelo formal del juego de dos jugadores |
| UCB sin Exploring Starts | Slides 12 | Tree policy dentro del árbol MCTS |
| Reward `× −1` al cambiar turno | Slides 12 | Propaga utilidad en juego zero-sum |
| Loop MCTS: 4 fases | Slides 13 | Núcleo de la búsqueda por turno |
| `argmax N` como acción final | Slides 13 | Retorno del algoritmo MCTS |
| Online Policy Improvement | Slides 13 | El agente mejora su política durante el turno |

---

## Estructura de archivos

```
Group Esteban/
├── policy.py        # Clase MCTSPolicy — interfaz con el torneo
├── mcts.py          # Motor MCTS: MCTSNode + MCTS (4 fases)
└── README.md        # Este archivo
```

---

## Requisitos

```
Python  >= 3.10
numpy   >= 1.24
```

No se requieren dependencias adicionales. El agente solo usa las librerías que ya utiliza el torneo.

---

## Instalación y ejecución

### 1. Activar el entorno (si usas Conda)

```bash
conda activate connect4_ia
```

### 2. Colocar la carpeta en el torneo

El agente debe estar en `tournament/groups/Group Esteban/`. El sistema de descubrimiento del torneo (`find_importable_classes`) lo detecta automáticamente por herencia de `Policy`.

```
tournament/
└── groups/
    ├── Group A/
    ├── Group B/
    ├── Group C/
    └── Group Esteban/   ← aquí van policy.py y mcts.py
        ├── policy.py
        └── mcts.py
```

### 3. Correr el torneo completo

```bash
cd tournament
python main.py
```

### 4. Correr una partida individual para pruebas

```python
import sys, numpy as np
sys.path.insert(0, ".")

from connect4.connect_state import ConnectState
from connect4.utils import find_importable_classes
from connect4.policy import Policy

participants = find_importable_classes("groups", Policy)

agent = participants["Group Esteban"](n_simulations=500)
agent.mount()

state = ConnectState()
while not state.is_final():
    action = agent.act(state.board)
    state = state.transition(action)

print("Ganador:", state.get_winner())   # -1 = rojo, 1 = amarillo, 0 = empate
```

---

## Parámetro configurable: `n_simulations`

El único parámetro del agente es el **presupuesto de simulaciones internas por turno**.

```python
# Instanciación con presupuesto personalizado
agent = MCTSPolicy(n_simulations=1000)
```

| Valor | Descripción | Win rate vs random (aprox.) |
|---|---|---|
| 50 | Muy rápido, menos preciso | ~100% |
| 100 | Rápido | ~100% |
| 500 | Balance (default) | ~100% |
| 1000 | Más fuerte, más lento | ~100% |
| 2000 | Máximo presupuesto | ~100% |

> El sweep completo de `n_simulations` con análisis de win rate y tiempo de cómputo se encuentra en `entrega.ipynb`.

---

## Convenciones del entorno

| Símbolo | Valor en `board[row, col]` | Descripción |
|---|---|---|
| Celda vacía | `0` | Sin ficha |
| Jugador rojo | `-1` | Mueve primero |
| Jugador amarillo | `+1` | Mueve segundo |

- El tablero es un `np.ndarray` de forma `(6, 7)`, fila 0 = fila superior.
- El jugador activo **no se pasa** a `act()` — se infiere contando fichas.
- Una partida dura como máximo 42 turnos (`T ≤ 42`), lo que garantiza horizonte finito.

---

## Diseño del MCTS — resumen técnico

Cada vez que el torneo llama a `act(board)`, el agente ejecuta `n_simulations` iteraciones del siguiente loop (slides 13):

```
for _ in range(n_simulations):
    1. Selection   → bajar por el árbol con UCB hasta nodo no expandido o terminal
    2. Expansion   → agregar un hijo nuevo al árbol
    3. Simulation  → rollout random (default policy) hasta estado final
    4. Backprop    → actualizar q̂ y N en el path con signo correcto (zero-sum)

return argmax_a N[raíz][a]   # acción más visitada
```

**Invariante clave:** los valores `q̂'` del sub-proceso interno **nunca** modifican el árbol de otra llamada. Cada `act()` construye un árbol nuevo desde cero — el agente es puramente online.

---

## Resultados de validación

Ejecutados antes de la entrega final:

| Escenario | Resultado |
|---|---|
| Victoria inmediata disponible (rojo) | Elige la columna correcta ✓ |
| Bloqueo de victoria del oponente | Elige la columna correcta ✓ |
| Victoria inmediata disponible (amarillo) | Elige la columna correcta ✓ |
| 60 partidas vs agente aleatorio (`n_sim=100`) | 60/60 victorias (100%) ✓ |
| 60 partidas vs agente aleatorio (`n_sim=500`) | 60/60 victorias (100%) ✓ |
| Pre-requisito mínimo del reto | Cumplido ✓ |

---

## Propuesta de mejora (para reporte)

La **default policy** actual es aleatoria pura. La mejora más directa, técnicamente razonable y sustentable, sería reemplazarla por una heurística ligera que priorice columnas centrales (el centro del tablero es estructuralmente más valioso en Connect-4). Esto aumentaría la calidad de los rollouts sin cambiar la arquitectura MCTS ni añadir conceptos fuera del curso.

---

*Fundamentos de Inteligencia Artificial — Universidad de La Sabana — 2026.1*
