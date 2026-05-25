# Connect-4 Agent — Juan Felipe Gómez

## Descripción

Agente inteligente para Connect-4 basado en **Monte Carlo Tree Search (MCTS) con UCT**, combinado con reglas de prioridad determinísticas y aprendizaje acumulativo entre partidas mediante una tabla-Q persistente.

El agente toma decisiones en tres capas de prioridad:

1. **Ganar inmediatamente** — si existe un movimiento ganador, lo juega (desempate: columna más central).
2. **Bloquear al oponente** — si el oponente puede ganar en el siguiente turno, lo bloquea.
3. **MCTS / UCT** — búsqueda en árbol con simulaciones aleatorias y fórmula UCT para posiciones sin solución inmediata.

Lo que diferencia a este agente de una implementación estándar de MCTS:

- **Tabla-Q persistente entre partidas** (`_q_table`): al finalizar cada juego, las estadísticas del árbol se guardan en un diccionario de clase. En la siguiente partida esas estadísticas se inyectan como *prior* en el UCT, acelerando la convergencia desde la primera simulación.
- **Hash Zobrist incremental**: el hash del tablero se actualiza con XOR en O(1) en cada expansión, evitando recalcularlo desde cero.
- **Inferencia automática de color**: el agente deduce si juega como Rojo (-1) o Amarillo (+1) comparando el conteo de fichas, sin requerir ningún parámetro externo.

## Estructura

```
juanfe/
├── policy.py       → lógica completa del agente (GomezAgent)
├── entrega.ipynb   → análisis experimental y gráficas
└── README.md       → este archivo
```

## Cómo ejecutar

Desde la raíz del repositorio del torneo:

```bash
python main.py
```

El agente se auto-descubre: basta con que `policy.py` esté en la carpeta correcta dentro de `groups/`. No se necesita registro manual ni `__init__.py`.

Para probar un enfrentamiento puntual sin correr el torneo completo:

```python
from connect4.policy import Policy
from connect4.utils import find_importable_classes
from tournament import play

participants = find_importable_classes("groups", Policy)
a = ("Gomez", participants["Gomez"])
b = ("OtroAgente", participants["OtroAgente"])
winner = play(a, b, best_of=7, first_player_distribution=0.5, seed=42)
print("Ganador:", winner[0])
```

## Configuración

### Presupuesto de tiempo (`TIME_BUDGET`)

Principal palanca de calidad vs. velocidad. Se cambia **antes** de instanciar agentes:

```python
GomezAgent.TIME_BUDGET = 2.0   # segundos por movimiento (default: 5.0)
```

| Parámetro | Valor por defecto | Descripción |
|-----------|:-----------------:|-------------|
| `TIME_BUDGET` | `5.0 s` | Tiempo máximo de búsqueda MCTS por movimiento en partidas locales |
| `_MAX_BUDGET` | `0.5 s` | Límite duro cuando el evaluador externo pasa un `timeout` |
| `_Q_MAX` | `300 000` | Máximo de entradas en la tabla-Q antes de detener el crecimiento |
| `_Q_MIN_VISITS` | `10` | Visitas mínimas para persistir un nodo en la tabla-Q |
| `C` (UCT) | `√2 ≈ 1.414` | Constante de exploración en la fórmula UCT |

### Tabla-Q

La tabla-Q acumula conocimiento entre partidas dentro del mismo proceso. Para reiniciarla (útil en experimentos aislados):

```python
GomezAgent._q_table.clear()
```

## Resultados

Los experimentos del notebook (`entrega.ipynb`) se corrieron con `TIME_BUDGET = 0.5 s`:

| Escenario | Color | Win% | Loss% |
|-----------|:-----:|:----:|:-----:|
| Gomez vs Aleatorio | Rojo | ~95% | 0% |
| Gomez vs Aleatorio | Amarillo | ~92% | 0% |
| Gomez vs Gomez | — | ~50% | ~50% |

- **Nunca pierde contra el jugador aleatorio** (0 derrotas en 200 partidas, ambos colores).
- **Win rate > 90%** en ambos colores con budget de solo 0.5 s.
- En autodesempeño el resultado es simétrico (~50/50), confirmando que no hay sesgos de implementación.


## Autor
**Juan Felipe Gómez**  