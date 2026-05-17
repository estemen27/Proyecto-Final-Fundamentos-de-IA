import math
import random
import time
import numpy as np
from connect4.policy import Policy

ROWS, COLS = 6, 7

# Zobrist table for O(1) incremental board hashing
_ZOB = np.random.default_rng(42).integers(0, 2**63, (ROWS, COLS, 3), dtype=np.uint64)
_ZOB_FLAT = _ZOB.reshape(ROWS * COLS, 3)


def _board_hash(board):
    idx = (board + 1).ravel()  # -1→0, 0→1, 1→2
    return int(np.bitwise_xor.reduce(_ZOB_FLAT[np.arange(ROWS * COLS), idx]))


def _valid_moves(board):
    return [c for c in range(COLS) if board[0, c] == 0]


def _drop_row(board, col):
    for r in range(ROWS - 1, -1, -1):
        if board[r, col] == 0:
            return r
    return -1


def _drop(board, col, player):
    b = board.copy()
    b[_drop_row(b, col), col] = player
    return b


def _winner(board):
    for r in range(ROWS):
        for c in range(COLS):
            p = board[r, c]
            if p == 0:
                continue
            if c + 3 < COLS and board[r, c+1] == p and board[r, c+2] == p and board[r, c+3] == p:
                return p
            if r + 3 < ROWS and board[r+1, c] == p and board[r+2, c] == p and board[r+3, c] == p:
                return p
            if r+3 < ROWS and c+3 < COLS and board[r+1,c+1] == p and board[r+2,c+2] == p and board[r+3,c+3] == p:
                return p
            if r+3 < ROWS and c-3 >= 0 and board[r+1,c-1] == p and board[r+2,c-2] == p and board[r+3,c-3] == p:
                return p
    return 0


def _wins_now(board, col, player):
    row = _drop_row(board, col)
    if row < 0:
        return False
    b = board.copy()
    b[row, col] = player
    return _winner(b) == player


def _rollout(board, player):
    b = board.copy()
    p = player
    while True:
        w = _winner(b)
        if w != 0:
            return w
        moves = _valid_moves(b)
        if not moves:
            return 0
        b = _drop(b, random.choice(moves), p)
        p = -p


class _Node:
    __slots__ = ('board', 'player', 'move', 'parent', 'children',
                 'untried', 'wins', 'visits', 'bhash')

    def __init__(self, board, player, move=None, parent=None, bhash=None):
        self.board = board
        self.player = player
        self.move = move
        self.parent = parent
        self.children = []
        self.untried = _valid_moves(board)
        random.shuffle(self.untried)
        self.wins = 0.0
        self.visits = 0
        self.bhash = bhash if bhash is not None else _board_hash(board)

    @property
    def is_terminal(self):
        return _winner(self.board) != 0 or not _valid_moves(self.board)

    @property
    def is_fully_expanded(self):
        return not self.untried

    def best_uct(self, c=1.414, q_table=None):
        log_n = math.log(self.visits)
        def uct(ch):
            score = ch.wins / ch.visits + c * math.sqrt(log_n / ch.visits)
            if q_table:
                entry = q_table.get((self.bhash, ch.move))
                if entry and entry[1]:
                    # Q-prior: decays as MCTS gathers its own data
                    score += 0.25 * (entry[0] / entry[1]) / (1.0 + ch.visits)
            return score
        return max(self.children, key=uct)

    def expand(self):
        col = self.untried.pop()
        row = _drop_row(self.board, col)
        # Incremental Zobrist hash: XOR out empty, XOR in player piece
        p_idx = 0 if self.player == -1 else 2
        new_hash = self.bhash ^ int(_ZOB[row, col, 1]) ^ int(_ZOB[row, col, p_idx])
        new_board = self.board.copy()
        new_board[row, col] = self.player
        child = _Node(new_board, -self.player, move=col, parent=self, bhash=new_hash)
        self.children.append(child)
        return child


_Q_MAX = 300_000    # cap total entries to avoid memory bloat
_Q_MIN_VISITS = 10  # only persist well-visited nodes (keeps flush fast)
_Q_FLUSH_SEC = 0.3  # hard cap on time spent flushing per act() call


def _flush_to_q(root, q_table):
    """Persist MCTS tree statistics into the class-level Q-table (time-capped)."""
    cutoff = time.time() + _Q_FLUSH_SEC
    stack = [root]
    while stack and time.time() < cutoff:
        node = stack.pop()
        if node.visits >= _Q_MIN_VISITS and node.parent is not None:
            key = (node.parent.bhash, node.move)
            if key in q_table or len(q_table) < _Q_MAX:
                if key not in q_table:
                    q_table[key] = [0.0, 0]
                q_table[key][0] += node.wins
                q_table[key][1] += node.visits
        for child in node.children:
            if child.visits >= _Q_MIN_VISITS:
                stack.append(child)


def _mcts(board, player, budget, q_table):
    root = _Node(board, player)
    deadline = time.time() + budget

    while time.time() < deadline:
        node = root

        while node.is_fully_expanded and not node.is_terminal:
            node = node.best_uct(q_table=q_table)

        if not node.is_terminal and not node.is_fully_expanded:
            node = node.expand()

        winner = _rollout(node.board, node.player)

        cur = node
        while cur is not None:
            cur.visits += 1
            if cur.parent is not None:
                mover = cur.parent.player
                if winner == mover:
                    cur.wins += 1.0
                elif winner == 0:
                    cur.wins += 0.5
            cur = cur.parent

    # Accumulate this run's knowledge into the shared Q-table
    _flush_to_q(root, q_table)

    if not root.children:
        moves = _valid_moves(board)
        return min(moves, key=lambda c: abs(c - 3))

    return max(root.children, key=lambda ch: ch.visits).move


class GomezAgent(Policy):
    TIME_BUDGET = 5.0
    _q_table = {}  # shared across all instances; persists across games in same process

    def __init__(self):
        try:
            super().__init__()
        except Exception:
            pass
        self.my_color = None
        self._budget = self.__class__.TIME_BUDGET

    def mount(self, timeout=None):
        self.my_color = None
        if timeout is not None:
            # Reserve 20% + flush window so act() never exceeds the hard limit
            self._budget = max(0.5, timeout * 0.80 - _Q_FLUSH_SEC)
        else:
            self._budget = self.__class__.TIME_BUDGET

    def _infer_color(self, board):
        return -1 if int(np.sum(board == -1)) == int(np.sum(board == 1)) else 1

    def act(self, board: np.ndarray) -> int:
        if self.my_color is None:
            self.my_color = self._infer_color(board)
        me = self.my_color
        moves = _valid_moves(board)

        if len(moves) == 1:
            return moves[0]

        for col in sorted(moves, key=lambda c: abs(c - 3)):
            if _wins_now(board, col, me):
                return col

        for col in sorted(moves, key=lambda c: abs(c - 3)):
            if _wins_now(board, col, -me):
                return col

        return _mcts(board, me, self._budget, self.__class__._q_table)
