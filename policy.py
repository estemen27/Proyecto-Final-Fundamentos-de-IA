import math
import numpy as np
from connect4.policy import Policy
from connect4.connect_state import ConnectState


class MCTSNode:

    __slots__ = (
        "state", "parent", "action_from_parent",
        "children", "untried_actions",
        "q", "n", "visits"
    )

    def __init__(self, state: ConnectState, parent=None, action_from_parent=None):
        self.state = state
        self.parent = parent
        self.action_from_parent = action_from_parent
        legal = state.get_free_cols()
        self.q = {a: 0.0 for a in legal}
        self.n = {a: 0   for a in legal}
        self.children = {}
        self.untried_actions = list(legal)
        self.visits = 0

    def is_fully_expanded(self) -> bool:
        return len(self.untried_actions) == 0

    def is_terminal(self) -> bool:
        return self.state.is_final()

    def ucb_score(self, action: int, c: float) -> float:
        if self.n[action] == 0:
            return float("inf")
        return self.q[action] + c * math.sqrt(math.log(self.visits) / self.n[action])

    def best_child_ucb(self, c: float) -> "MCTSNode":
        return max(
            self.children.values(),
            key=lambda child: self.ucb_score(child.action_from_parent, c)
        )

    def best_action(self) -> int:
        return max(self.n, key=lambda a: self.n[a])


class MCTS:

    def __init__(self, n_simulations: int, c: float):
        self.n_simulations = n_simulations
        self.c = c

    def search(self, root_state: ConnectState) -> int:
        root = MCTSNode(root_state)

        for _ in range(self.n_simulations):
            node = self._select(root)

            if not node.is_terminal():
                node = self._expand(node)

            reward = self._simulate(node.state)
            self._backprop(node, reward)

        return root.best_action()

    def _select(self, node: MCTSNode) -> MCTSNode:
        while not node.is_terminal() and node.is_fully_expanded():
            node = node.best_child_ucb(self.c)
        return node

    def _expand(self, node: MCTSNode) -> MCTSNode:
        action = node.untried_actions.pop(
            np.random.randint(len(node.untried_actions))
        )
        next_state = node.state.transition(action)
        child = MCTSNode(next_state, parent=node, action_from_parent=action)
        node.children[action] = child
        return child

    def _simulate(self, state: ConnectState) -> float:
        sim_state = state
        while not sim_state.is_final():
            action = int(np.random.choice(sim_state.get_free_cols()))
            sim_state = sim_state.transition(action)
        return float(sim_state.get_winner())

    def _backprop(self, node: MCTSNode, reward: float) -> None:
        current = node
        while current.parent is not None:
            action = current.action_from_parent
            parent = current.parent
            local_reward = reward * parent.state.player
            parent.n[action] += 1
            parent.visits += 1
            parent.q[action] += (local_reward - parent.q[action]) / parent.n[action]
            current = parent

        root = node
        while root.parent is not None:
            root = root.parent
        root.visits = sum(root.n.values())


class MCTSPolicy(Policy):

    def __init__(self, n_simulations: int = 500, c: float = math.sqrt(2)):
        self.n_simulations = n_simulations
        self.c = c
        self._mcts = MCTS(n_simulations=self.n_simulations, c=self.c)

    def mount(self, *args, **kwargs) -> None:
        self._mcts = MCTS(n_simulations=self.n_simulations, c=self.c)

    def act(self, s: np.ndarray) -> int:
        player = self._infer_player(s)
        state = ConnectState(board=s, player=player)
        return self._mcts.search(state)

    def _infer_player(self, board: np.ndarray) -> int:
        reds    = int(np.sum(board == -1))
        yellows = int(np.sum(board ==  1))
        return -1 if reds == yellows else 1
