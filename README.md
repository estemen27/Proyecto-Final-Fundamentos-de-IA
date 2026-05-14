# Connect-4 Reactive Heuristic Agent

## Idea General

Este agente sigue un enfoque reactivo basado en evaluación inmediata del tablero en lugar de búsqueda profunda o simulaciones Monte Carlo.

La decisión se toma asignando un puntaje a cada acción disponible usando un conjunto configurable de reglas y prioridades heurísticas.

El objetivo es estudiar cómo diferentes configuraciones y estrategias afectan el desempeño del agente contra distintos oponentes.

---

# Filosofía del Agente

El agente:

- no construye un árbol de búsqueda profundo,
- no intenta predecir muchas jugadas futuras,
- y no utiliza aprendizaje estadístico.

En cambio:

- evalúa el estado actual,
- detecta amenazas y oportunidades inmediatas,
- asigna un score a cada movimiento,
- y selecciona la acción con mayor utilidad heurística.

Esto permite:

- decisiones rápidas,
- comportamiento interpretable,
- análisis modular,
- comparación experimental entre configuraciones.

---

# Estrategia General

Cada movimiento posible recibe un puntaje calculado con reglas parametrizables.

Ejemplo conceptual:

score(action) =

    win_weight * immediate_win +

    block_weight * immediate_block +

    center_weight * center_priority +

    threat_weight * threat_creation +

    safety_weight * safe_move

La acción final es:

argmax(score(action))

---

# Heurísticas del Agente

## 1. Immediate Win

Si una acción genera victoria inmediata:

- prioridad máxima.

Parámetro:

- `WIN_WEIGHT`

---

## 2. Immediate Block

Si el oponente puede ganar en el siguiente turno:

- bloquear esa jugada.

Parámetro:

- `BLOCK_WEIGHT`

---

## 3. Center Preference

Las columnas centrales suelen generar más conexiones potenciales.

El agente puede priorizar:

- columnas centrales,
- control posicional.

Parámetro:

- `CENTER_WEIGHT`

---

## 4. Threat Creation

El agente favorece jugadas que generan:

- 2 en línea,
- 3 en línea,
- múltiples amenazas futuras.

Parámetro:

- `THREAT_WEIGHT`

---

## 5. Safe Move Filtering

Evita movimientos que permitan:

- victoria inmediata del rival,
- aperturas peligrosas.

Parámetro:

- `SAFETY_WEIGHT`

---

# Configuraciones Experimentales

El agente permite activar/desactivar reglas y modificar pesos heurísticos para estudiar el impacto en el desempeño.

Ejemplos:

## Configuración ofensiva

- THREAT_WEIGHT alto
- BLOCK_WEIGHT moderado

Busca maximizar presión ofensiva.

---

## Configuración defensiva

- BLOCK_WEIGHT alto
- SAFETY_WEIGHT alto

Prioriza supervivencia y control.

---

## Configuración balanceada

Pesos intermedios entre ataque y defensa.

---

# Variables de Análisis

Se planea analizar:

- porcentaje de victorias vs agente aleatorio,
- desempeño jugando primero y segundo,
- tiempo promedio de decisión,
- impacto de cada heurística,
- comparación entre configuraciones,
- desempeño contra sí mismo.

---

# Hipótesis

Posibles hipótesis experimentales:

- priorizar el centro mejora el win rate,
- estrategias ofensivas ganan más rápido pero son menos seguras,
- bloquear amenazas inmediatas tiene alto impacto,
- agregar demasiadas heurísticas aumenta costo computacional con poca mejora.

---

# Diferenciación Conceptual

Este agente se diferencia de enfoques basados en:

- Monte Carlo Tree Search (MCTS),
- búsqueda adversarial profunda,
- simulaciones probabilísticas,
- reinforcement learning.

El enfoque principal aquí es:

- evaluación heurística local,
- toma de decisiones reactiva,
- comportamiento interpretable y configurable.
