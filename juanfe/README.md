# Connect-4 Agent — Juan Felipe Gómez

## Descripción

Agente inteligente para Connect-4 que combina **seis capas de decisión** en orden de prioridad estricta: cinco reglas deterministas que resuelven situaciones tácticas sin consumir tiempo de búsqueda, y MCTS/UCT con tabla-Q persistente entre partidas para las posiciones complejas restantes.

### Capas de decisión

| Prioridad | Capa | Descripción |
|-----------|------|-------------|
| 1° | **Libro de apertura** | Los primeros 1–3 movimientos son fijos (centro o columna adyacente). Connect-4 está matemáticamente resuelto; comenzar en el centro garantiza ventaja posicional. |
| 2° | **Victoria inmediata** | Si hay un movimiento ganador, se juega (desempate: columna más central). |
| 3° | **Bloqueo inmediato** | Si el oponente puede ganar en su siguiente turno, se bloquea. |
| 4° | **Fork propio** | Si se puede crear dos amenazas simultáneas (el rival solo puede tapar una), se crea el fork. |
| 5° | **Bloqueo de fork** | Si el oponente puede crear un fork en su siguiente turno, se previene. |
| 6° | **MCTS / UCT + Q-table** | Búsqueda en árbol con simulaciones aleatorias y Q-prior entre partidas. |

Las capas 1–5 son **O(1) en tiempo de búsqueda**. Solo si ninguna aplica se invoca MCTS.

### Diferencias respecto a una implementación estándar de MCTS

- **Tabla-Q persistente entre partidas** (`_q_table`): atributo de clase que acumula estadísticas del árbol MCTS al finalizar cada juego. En la siguiente partida esas estadísticas se inyectan como *prior* en la fórmula UCT, acelerando la convergencia desde la primera simulación.
- **Hash Zobrist incremental**: el hash del tablero se actualiza con XOR en O(1) en cada expansión del árbol, evitando recalcularlo desde cero y haciendo viable la Q-table.
- **Inferencia automática de color**: el agente deduce si juega como Rojo (-1) o Amarillo (+1) comparando el conteo de fichas, sin requerir parámetro externo.
- **Presupuesto adaptativo**: cuando `mount(timeout=N)` recibe un límite total, el tiempo por movimiento se calcula dividiendo el tiempo restante entre los movimientos estimados que quedan, distribuyendo el presupuesto de forma óptima a lo largo de la partida.

## Diferencias frente a los otros agentes del torneo

**Group A (FVMCPolicy)** usa Monte Carlo *plano* (flat MC): lanza 500 simulaciones aleatorias directamente desde la raíz sin construir un árbol, actualizando un Q-value promedio por par (estado, acción). Al no construir árbol, no puede enfocar simulaciones en las ramas prometedoras ni reutilizar trabajo entre movimientos. Además usa `board.tobytes()` como clave de hash (60 bytes de comparación por lookup) frente al hash Zobrist de GomezAgent (un entero de 64 bits, O(1)), y su Q-table es por instancia: se borra al inicio de cada partida. No tiene reglas de prioridad.

**Group B (SantiPolicy)** usa minimax con poda alfa-beta a profundidad fija 3. Es determinista y exhaustivo dentro de esas 3 capas pero no puede ver más allá sin coste exponencial. La función de evaluación heurística (control de centro, 2-en-línea, 3-en-línea) puede asignar puntuaciones incorrectas en posiciones donde el resultado está más allá de 3 movimientos, lo que produce errores en medio-juego. No tiene aprendizaje entre partidas ni detección de forks.

**GomezAgent** combina lo mejor de ambos enfoques: las reglas deterministas de Group B (ganar, bloquear) extendidas con detección de forks, más la búsqueda estocástica de Group A elevada a búsqueda en árbol UCT sin límite de profundidad, más aprendizaje cross-game mediante la Q-table de clase. El resultado es un agente que resuelve tácticamente las posiciones simples en tiempo cero y usa todo el presupuesto de tiempo en las posiciones que realmente lo requieren.

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

Para probar un enfrentamiento puntual:

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
GomezAgent.TIME_BUDGET = 10.0   # segundos por movimiento (default)
```

| Parámetro | Valor por defecto | Descripción |
|-----------|:-----------------:|-------------|
| `TIME_BUDGET` | `10.0 s` | Tiempo máximo de búsqueda MCTS por movimiento en partidas locales |
| `_MAX_BUDGET` | `10.0 s` | Límite duro cuando el evaluador externo pasa un `timeout` |
| `_Q_MAX` | `300 000` | Máximo de entradas en la tabla-Q antes de detener el crecimiento |
| `_Q_MIN_VISITS` | `10` | Visitas mínimas para persistir un nodo en la tabla-Q |
| `C` (UCT) | `√2 ≈ 1.414` | Constante de exploración en la fórmula UCT |

### Tabla-Q

La tabla-Q acumula conocimiento entre partidas dentro del mismo proceso. Para reiniciarla:

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
