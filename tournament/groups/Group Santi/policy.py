import numpy as np
from connect4.policy import Policy
from connect4.connect_state import ConnectState
import random


class SantiPolicy(Policy):
    """Policy basada en minimax con un DEPTH que sirve de tipo lookahead."""

    DEPTH = 3

    CENTER_WEIGHT = 1
    TWO_IN_ROW_WEIGHT = 2
    THREE_IN_ROW_WEIGHT = 6
    OPP_THREE_PENALTY = 5

    WIN_SCORE = 30
    LOSS_SCORE = -30

    def mount(self, timeout: float | None = None) -> None:
        pass

    def _infer_player(self, board: np.ndarray) -> int:
        # Deduce el signo del jugador que debe mover
        n_neg = np.count_nonzero(board == -1)
        n_pos = np.count_nonzero(board == 1)
        # -1 comienza primero; si hay menos o igual -1 que 1 es el turno de -1
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

    def _evaluate_board(self, board: np.ndarray, player: int) -> float:
        """Evalua posicion no terminal desde la perspectiva de `player`."""
        score = 0.0

        # Control del centro
        center_col = board[:, 3]
        score += self.CENTER_WEIGHT * np.count_nonzero(center_col == player)
        score -= self.CENTER_WEIGHT * np.count_nonzero(center_col == -player)

        my_two = self._count_windows(board, player, 2)
        my_three = self._count_windows(board, player, 3)
        opp_three = self._count_windows(board, -player, 3)

        score += self.TWO_IN_ROW_WEIGHT * my_two
        score += self.THREE_IN_ROW_WEIGHT * my_three
        score -= self.OPP_THREE_PENALTY * opp_three

        return score

    def _minimax(
        self,
        state: ConnectState,
        depth: int,
        alpha: float,
        beta: float,
        maximizing: bool,
        root_player: int,
    ) -> float:
        winner = state.get_winner()
        if winner == root_player:
            return self.WIN_SCORE + depth
        if winner == -root_player:
            return self.LOSS_SCORE - depth
        if depth == 0 or state.is_final():
            return self._evaluate_board(state.board, root_player)

        available = state.get_free_cols()
        if not available:
            return self._evaluate_board(state.board, root_player)

        # Ordena columnas priorizando centro para mejorar poda y decision.
        ordered_moves = sorted(available, key=lambda c: abs(3 - c))

        if maximizing:
            # Turno del agente: se queda con la jugada que mas le conviene.
            value = float("-inf")
            for col in ordered_moves:
                child = state.transition(int(col))
                value = max(
                    value,
                    self._minimax(child, depth - 1, alpha, beta, False, root_player),
                )
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value

        # Turno del rival: asume la respuesta mas incomoda para el agente.
        value = float("inf")
        for col in ordered_moves:
            child = state.transition(int(col))
            value = min(
                value,
                self._minimax(child, depth - 1, alpha, beta, True, root_player),
            )
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

    def act(self, s: np.ndarray) -> int:
        board = np.array(s)
        player = self._infer_player(board)
        state = ConnectState(board, player)

        available = state.get_free_cols()
        if not available:
            # Fallback
            rng = np.random.default_rng()
            return int(rng.integers(0, 7))

        # Victoria inmediata si hay
        for col in available:
            nxt = state.transition(int(col))
            if nxt.get_winner() == player:
                return int(col)

        best_score = float("-inf")
        best_cols = []
        ordered_moves = sorted(available, key=lambda c: abs(3 - c))

        for col in ordered_moves:
            next_state = state.transition(int(col))
            score = self._minimax(
                next_state,
                max(0, int(self.DEPTH) - 1),
                float("-inf"),
                float("inf"),
                False,
                player,
            )

            if score > best_score:
                best_score = score
                best_cols = [col]
            elif score == best_score:
                best_cols.append(col)

        # Desempate aleatorio
        if best_cols:
            return int(random.choice(best_cols))
        return int(random.choice(available))
