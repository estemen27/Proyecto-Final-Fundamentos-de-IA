import numpy as np
from connect4.policy import Policy
from connect4.connect_state import ConnectState

ROWS, COLS = 6, 7


def _window_score(window, player):
    mine  = window.count(player)
    empty = window.count(0)
    if mine == 3 and empty == 1: return 0.4
    if mine == 2 and empty == 2: return 0.05
    return 0.0


def _heuristic(board, player):
    s = 0.0
    for r in range(ROWS):
        for c in range(COLS - 3):
            s += _window_score([int(board[r][c + i]) for i in range(4)], player)
    for r in range(ROWS - 3):
        for c in range(COLS):
            s += _window_score([int(board[r + i][c]) for i in range(4)], player)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            s += _window_score([int(board[r + i][c + i]) for i in range(4)], player)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            s += _window_score([int(board[r - i][c + i]) for i in range(4)], player)
    return s


def _shape(board):
    return _heuristic(board, 1) - _heuristic(board, -1)


def _random_action(state):
    return int(np.random.choice(state.get_free_cols()))


class FVMCPolicy(Policy):

    def __init__(self, n_trials: int = 500, shaping_weight: float = 0.1,
                 max_rollout: int = 50):
        self.n_trials       = n_trials
        self.shaping_weight = shaping_weight
        self.max_rollout    = max_rollout
        self.Q = {}
        self.N = {}

    def mount(self, *args, **kwargs) -> None:
        pass

    def act(self, s: np.ndarray) -> int:
        player = self._infer_player(s)
        root   = ConnectState(board=s, player=player)
        legal  = root.get_free_cols()
        key0   = root.board.tobytes()

        for _ in range(self.n_trials):
            a0 = legal[np.random.randint(len(legal))]
            self._trial(root, a0)

        scores = [self.Q.get((key0, a), 0.0) for a in legal]
        return legal[int(np.argmax(scores))]

    def _trial(self, root, a0) -> None:
        traj  = []
        state = root
        a     = a0

        for _ in range(self.max_rollout):
            traj.append((state, a))
            state = state.transition(a)
            if state.is_final():
                break
            a = _random_action(state)

        terminal = float(state.get_winner()) if state.is_final() else 0.0
        U_abs    = terminal + self.shaping_weight * _shape(state.board)

        seen = set()
        for st, ac in traj:
            key = (st.board.tobytes(), ac)
            if key in seen:
                continue
            seen.add(key)
            U_local = U_abs * st.player
            if key not in self.N:
                self.Q[key] = 0.0
                self.N[key] = 0
            self.N[key] += 1
            self.Q[key] += (U_local - self.Q[key]) / self.N[key]

    @staticmethod
    def _infer_player(board: np.ndarray) -> int:
        reds    = int(np.sum(board == -1))
        yellows = int(np.sum(board ==  1))
        return -1 if reds == yellows else 1
