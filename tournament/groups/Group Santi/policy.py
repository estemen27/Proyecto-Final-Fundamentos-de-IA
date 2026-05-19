import numpy as np
from connect4.policy import Policy
from connect4.connect_state import ConnectState
import random


class SantiPolicy(Policy):
    """Agente reactivo heurístico configurable.

    Implementa las heurísticas descritas en el README:
      - Immediate Win
      - Immediate Block
      - Center Preference
      - Threat Creation (counts de ventanas de 2/3)
      - Safe Move Filtering (evita jugadas que permitan mate inmediato)

    Los pesos por defecto pueden ajustarse editando las constantes de clase.
    """

    WIN_WEIGHT = 10000.0
    BLOCK_WEIGHT = 9000.0
    CENTER_WEIGHT = 3.0
    THREAT_WEIGHT_2 = 1.0
    THREAT_WEIGHT_3 = 5.0
    SAFETY_PENALTY = 10000.0
    
    PRESETS = {
        "offensive": {
            "WIN_WEIGHT": 10000.0,
            "BLOCK_WEIGHT": 5000.0,
            "CENTER_WEIGHT": 4.0,
            "THREAT_WEIGHT_2": 1.0,
            "THREAT_WEIGHT_3": 8.0,
            "SAFETY_PENALTY": 8000.0,
        },
        "defensive": {
            "WIN_WEIGHT": 10000.0,
            "BLOCK_WEIGHT": 12000.0,
            "CENTER_WEIGHT": 2.0,
            "THREAT_WEIGHT_2": 0.5,
            "THREAT_WEIGHT_3": 3.0,
            "SAFETY_PENALTY": 20000.0,
        },
        "balanced": {
            "WIN_WEIGHT": 10000.0,
            "BLOCK_WEIGHT": 9000.0,
            "CENTER_WEIGHT": 3.0,
            "THREAT_WEIGHT_2": 1.0,
            "THREAT_WEIGHT_3": 5.0,
            "SAFETY_PENALTY": 10000.0,
        },
    }

    MODE: str | None = None

    @classmethod
    def apply_preset(cls, name: str) -> None:
        """Apply a preset by name, setting class-level weights.

        This updates class attributes so subsequent instantiations use the preset.
        """
        presets = getattr(cls, "PRESETS", {})
        if name not in presets:
            raise ValueError(f"Preset {name} not found. Available: {list(presets.keys())}")
        for k, v in presets[name].items():
            setattr(cls, k, v)
        cls.MODE = name

    def mount(self, timeout: float | None = None) -> None:
        # Inicialización si se requiere (por ejemplo cargar parámetros desde archivo).
        pass

    def _infer_player(self, board: np.ndarray) -> int:
        # Deduce el signo del jugador que debe mover (y por tanto el signo de esta política)
        n_neg = np.count_nonzero(board == -1)
        n_pos = np.count_nonzero(board == 1)
        # -1 comienza primero; si hay menos o igual -1 que 1 -> es el turno de -1
        return -1 if n_neg <= n_pos else 1

    def _count_windows(self, board: np.ndarray, player: int, length: int) -> int:
        rows, cols = board.shape
        count = 0
        # Horizontal
        for r in range(rows):
            for c in range(cols - 3):
                window = board[r, c : c + 4]
                if np.count_nonzero(window == -player) == 0 and np.count_nonzero(window == player) == length:
                    count += 1
        # Vertical
        for c in range(cols):
            for r in range(rows - 3):
                window = board[r : r + 4, c]
                if np.count_nonzero(window == -player) == 0 and np.count_nonzero(window == player) == length:
                    count += 1
        # Diagonal right-down
        for r in range(rows - 3):
            for c in range(cols - 3):
                window = np.array([board[r + i, c + i] for i in range(4)])
                if np.count_nonzero(window == -player) == 0 and np.count_nonzero(window == player) == length:
                    count += 1
        # Diagonal left-down
        for r in range(rows - 3):
            for c in range(3, cols):
                window = np.array([board[r + i, c - i] for i in range(4)])
                if np.count_nonzero(window == -player) == 0 and np.count_nonzero(window == player) == length:
                    count += 1
        return count

    def act(self, s: np.ndarray) -> int:
        board = np.array(s)
        player = self._infer_player(board)
        opponent = -player
        state = ConnectState(board, player)

        available = state.get_free_cols()
        if not available:
            # Fallback aleatorio si no hay columnas (aunque normalmente no sucede porque is_final previene)
            rng = np.random.default_rng()
            return int(rng.integers(0, 7))

        best_score = None
        best_cols = []

        for col in available:
            # Simula la jugada
            try:
                new_state = state.transition(int(col))
            except ValueError:
                continue

            score = 0.0

            # Immediate win
            if new_state.get_winner() == player:
                score += self.WIN_WEIGHT

            # Immediate block: si tras mi jugada el oponente tiene una jugada que le da victoria, la bloqueamos
            # (se valora alto como bloqueo)
            # Para block: comprobar si existe una columna que haga ganar al oponente en su turno
            opponent_can_win = False
            for c2 in new_state.get_free_cols():
                try:
                    s2 = new_state.transition(int(c2))
                except ValueError:
                    continue
                if s2.get_winner() == opponent:
                    opponent_can_win = True
                    break
            if opponent_can_win:
                score += self.BLOCK_WEIGHT

            # Center preference (col 3 es el centro)
            center_score = (3 - abs(col - 3)) * self.CENTER_WEIGHT
            score += center_score

            # Threat creation: contar ventanas con 2 y 3 fichas propias (sin fichas enemigas)
            n2 = self._count_windows(new_state.board, player, 2)
            n3 = self._count_windows(new_state.board, player, 3)
            score += n2 * self.THREAT_WEIGHT_2 + n3 * self.THREAT_WEIGHT_3

            # Safety filtering: si la jugada permite que el rival gane inmediatamente (en su siguiente), penalizar
            # Aquí buscamos si tras mi movimiento el oponente tiene una jugada ganadora -> gran penalización
            allows_opponent_win = False
            for c2 in new_state.get_free_cols():
                try:
                    s2 = new_state.transition(int(c2))
                except ValueError:
                    continue
                if s2.get_winner() == opponent:
                    allows_opponent_win = True
                    break
            if allows_opponent_win:
                score -= self.SAFETY_PENALTY

            if best_score is None or score > best_score:
                best_score = score
                best_cols = [col]
            elif score == best_score:
                best_cols.append(col)

        # Elegir aleatoriamente entre los mejores empates.
        # Si por alguna razón no quedó ninguna opción evaluada, caer en una columna legal.
        if best_cols:
            return int(random.choice(best_cols))
        return int(random.choice(available))
