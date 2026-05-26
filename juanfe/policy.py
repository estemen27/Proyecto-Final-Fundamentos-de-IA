import math
import random
import time
import numpy as np
from connect4.policy import Policy

ROWS, COLS = 6, 7
CENTER = COLS // 2  

# TABLA ZOBRIST — hashing incremental
# Asigna un numero de 64 bits aleatorio a cada combinacion (fila, col, pieza).

_ZOB      = np.random.default_rng(42).integers(0, 2**63, (ROWS, COLS, 3), dtype=np.uint64)
_ZOB_FLAT = _ZOB.reshape(ROWS * COLS, 3)


# HELPERS DE TABLERO

def _board_hash(board):
    """Hash Zobrist completo del tablero (usado solo en la raiz del arbol)."""
    idx = (board + 1).ravel()
    return int(np.bitwise_xor.reduce(_ZOB_FLAT[np.arange(ROWS * COLS), idx]))


def _valid_moves(board):
    """Columnas donde se puede colocar una ficha (fila superior libre)."""
    return [c for c in range(COLS) if board[0, c] == 0]


def _drop_row(board, col):
    """Fila en la que caeria una ficha en la columna col (gravedad)."""
    for r in range(ROWS - 1, -1, -1):
        if board[r, col] == 0:
            return r
    return -1  


def _drop(board, col, player):
    """Retorna copia del tablero tras colocar la ficha de player en col."""
    b = board.copy()
    b[_drop_row(b, col), col] = player
    return b


def _winner(board):
    """
    Escanea el tablero buscando cuatro en linea.
    Retorna -1, 1, o 0 si no hay ganador aun.
    """
    for r in range(ROWS):
        for c in range(COLS):
            p = board[r, c]
            if p == 0:
                continue
            if c+3 < COLS and board[r,c+1]==p and board[r,c+2]==p and board[r,c+3]==p:
                return p
            if r+3 < ROWS and board[r+1,c]==p and board[r+2,c]==p and board[r+3,c]==p:
                return p
            if r+3 < ROWS and c+3 < COLS and board[r+1,c+1]==p and board[r+2,c+2]==p and board[r+3,c+3]==p:
                return p
            if r+3 < ROWS and c-3 >= 0 and board[r+1,c-1]==p and board[r+2,c-2]==p and board[r+3,c-3]==p:
                return p
    return 0


def _wins_now(board, col, player):
    """True si colocar una ficha de player en col resulta en victoria inmediata."""
    row = _drop_row(board, col)
    if row < 0:
        return False
    b = board.copy()
    b[row, col] = player
    return _winner(b) == player



def _opening_move(board, player):
    """
    Retorna la jugada optima de apertura, o None si no aplica.
    Solo activo cuando el tablero tiene 0-2 piezas.
    """
    pieces = int(np.count_nonzero(board))

    # Turno 1 (tablero vacio): siempre al centro, garantiza ventaja posicional
    if pieces == 0:
        return CENTER

    # Turno 2 (1 pieza en el tablero):
    if pieces == 1:
        # Si el oponente tomo el centro, jugar columna adyacente
        if board[ROWS - 1, CENTER] != 0:
            return CENTER + 1
        # Si el oponente no tomo el centro, tomarlo
        return CENTER

    # Turno 3 (2 piezas): tomar el centro si sigue libre
    if pieces == 2 and board[ROWS - 1, CENTER] == 0:
        return CENTER

    return None  # fuera del rango del libro de apertura


# DETECCION DE FORKS (DOBLES AMENAZAS)
# Un fork ocurre cuando un jugador crea dos amenazas ganadoras simultaneas.
# El oponente solo puede bloquear una, asi que la otra gana la partida.

def _creates_fork(board, col, player):
    """
    True si colocar player en col genera 2 o mas amenazas ganadoras simultaneas.
    El oponente no puede bloquear ambas, garantizando victoria en el proximo turno.
    """
    row = _drop_row(board, col)
    if row < 0:
        return False
    b = board.copy()
    b[row, col] = player
    threats = sum(1 for c in _valid_moves(b) if _wins_now(b, c, player))
    return threats >= 2


def _best_fork_move(board, moves, player):
    """
    Busca el mejor movimiento que crea un fork para player.
    Desempate por columna mas central (mayor control posicional).
    Retorna la columna o None si no existe fork posible.
    """
    fork_cols = [c for c in moves if _creates_fork(board, c, player)]
    if not fork_cols:
        return None
    return min(fork_cols, key=lambda c: abs(c - CENTER))


def _best_fork_block(board, moves, player):
    """
    Busca el movimiento que bloquea el fork del oponente.
    Si el oponente puede crear un fork en su proximo turno, hay que impedirlo.
    Retorna la columna o None si el oponente no puede hacer fork.
    """
    opp = -player
    fork_blocks = [c for c in moves if _creates_fork(board, c, opp)]
    if not fork_blocks:
        return None
    return min(fork_blocks, key=lambda c: abs(c - CENTER))


def _rollout(board, player):
    b, p = board.copy(), player
    while True:
        w = _winner(b)
        if w != 0:
            return w
        ms = _valid_moves(b)
        if not ms:
            return 0
        b = _drop(b, random.choice(ms), p)
        p = -p


# NODO DEL ARBOL MCTS

class _Node:
    __slots__ = ('board', 'player', 'move', 'parent', 'children',
                 'untried', 'wins', 'visits', 'bhash')

    def __init__(self, board, player, move=None, parent=None, bhash=None):
        self.board    = board
        self.player   = player
        self.move     = move
        self.parent   = parent
        self.children = []
        self.untried  = _valid_moves(board)
        random.shuffle(self.untried)
        self.wins     = 0.0
        self.visits   = 0
        self.bhash    = bhash if bhash is not None else _board_hash(board)

    @property
    def is_terminal(self):
        return _winner(self.board) != 0 or not _valid_moves(self.board)

    @property
    def is_fully_expanded(self):
        return not self.untried

    def best_uct(self, c=1.414, q_table=None):
        log_n = math.log(self.visits)

        def score(ch):
            uct = ch.wins / ch.visits + c * math.sqrt(log_n / ch.visits)
            if q_table:
                entry = q_table.get((self.bhash, ch.move))
                if entry and entry[1] > 0:
                    uct += 0.25 * (entry[0] / entry[1]) / (1.0 + ch.visits)
            return uct

        return max(self.children, key=score)

    def expand(self):
        col       = self.untried.pop()
        row       = _drop_row(self.board, col)
        p_idx     = 0 if self.player == -1 else 2
        new_hash  = self.bhash ^ int(_ZOB[row, col, 1]) ^ int(_ZOB[row, col, p_idx])
        new_board = self.board.copy()
        new_board[row, col] = self.player
        child = _Node(new_board, -self.player, move=col, parent=self, bhash=new_hash)
        self.children.append(child)
        return child


# Q-TABLE: aprendizaje persistente entre partidas

_Q_MAX        = 300_000
_Q_MIN_VISITS = 10
_Q_FLUSH_SEC  = 0.3


def _flush_to_q(root, q_table):
    """
    Recorre el arbol MCTS en DFS y persiste los nodos fiables en q_table.
    Limitado por tiempo para no penalizar el proximo movimiento.
    """
    cutoff = time.time() + _Q_FLUSH_SEC
    stack  = [root]
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


# MOTOR MCTS PRINCIPAL

def _mcts(board, player, budget, q_table):
    root     = _Node(board, player)
    deadline = time.time() + budget

    while time.time() < deadline:
        node = root

        # 1. SELECCION
        while node.is_fully_expanded and not node.is_terminal:
            node = node.best_uct(q_table=q_table)

        # 2. EXPANSION
        if not node.is_terminal and not node.is_fully_expanded:
            node = node.expand()

        # 3. SIMULACION
        winner = _rollout(node.board, node.player)

        # 4. RETROPROPAGACION
        cur = node
        while cur is not None:
            cur.visits += 1
            if cur.parent is not None:
                mover = cur.parent.player
                if winner == mover:  cur.wins += 1.0
                elif winner == 0:    cur.wins += 0.5
            cur = cur.parent

    _flush_to_q(root, q_table)

    if not root.children:
        return min(_valid_moves(board), key=lambda c: abs(c - CENTER))

    return max(root.children, key=lambda ch: ch.visits).move


# AGENTE PRINCIPAL

class LosConvolucionales(Policy):
    TIME_BUDGET      = 10.0
    _MAX_BUDGET      = 10.0
    _q_table         = {}

    def __init__(self):
        try:
            super().__init__()
        except Exception:
            pass
        self.my_color     = None
        self._budget      = self.__class__.TIME_BUDGET
        self._game_start  = None
        self._game_budget = None

    def mount(self, timeout=None):
        self.my_color    = None
        self._game_start = time.time()
        if timeout is not None:
            self._game_budget = timeout * 0.85
            self._budget      = min(self.__class__._MAX_BUDGET, self._game_budget / 20)
        else:
            self._game_budget = None
            self._budget      = self.__class__.TIME_BUDGET

    def _infer_color(self, board):
        reds = int(np.sum(board == -1))
        yels = int(np.sum(board ==  1))
        return -1 if reds == yels else 1

    def _adapted_budget(self, board):
        if self._game_budget is not None and self._game_start is not None:
            elapsed    = time.time() - self._game_start
            remaining  = max(0.05, self._game_budget - elapsed)
            empty      = int(np.sum(board == 0))
            moves_left = max(1, empty // 2)
            return min(self.__class__._MAX_BUDGET, remaining / moves_left)
        return self._budget

    def act(self, board: np.ndarray) -> int:
        if self.my_color is None:
            self.my_color = self._infer_color(board)

        me    = self.my_color
        moves = _valid_moves(board)

        if len(moves) == 1:
            return moves[0]

        # Capa 1: Libro de apertura
        opening = _opening_move(board, me)
        if opening is not None and opening in moves:
            return opening

        # Capa 2: Victoria inmediata
        for col in sorted(moves, key=lambda c: abs(c - CENTER)):
            if _wins_now(board, col, me):
                return col

        # Capa 3: Bloquear victoria inmediata del oponente
        for col in sorted(moves, key=lambda c: abs(c - CENTER)):
            if _wins_now(board, col, -me):
                return col

        # Capa 4: Crear fork (dos amenazas simultaneas)
        fork_move = _best_fork_move(board, moves, me)
        if fork_move is not None:
            return fork_move

        # Capa 5: Bloquear fork del oponente
        fork_block = _best_fork_block(board, moves, me)
        if fork_block is not None:
            return fork_block

        # Capa 6: MCTS + RAVE + Q-table
        budget = self._adapted_budget(board)
        return _mcts(board, me, budget, self.__class__._q_table)
