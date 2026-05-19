# Agente MCTS — Connect-4
### Fundamentos de Inteligencia Artificial 
**Autor:** Esteban Bernal Cortés

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

