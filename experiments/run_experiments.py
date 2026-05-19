"""Herramienta para ejecutar barridos de parámetros y generar resultados para análisis.

Uso básico desde Python:
    from experiments.run_experiments import param_grid_search
    param_grid_search(SantiPolicy, SantiPolicy, grid, n_games_per_combo=300)

Genera archivos JSON en `experiments/results/` con métricas agregadas.
"""
from __future__ import annotations

import os
import sys
import json
import itertools
import inspect
from datetime import datetime
from multiprocessing import Pool
from typing import Any, Dict, Iterable

import numpy as np

# When running from experiments/, ensure project root and tournament/ are on sys.path
_THIS_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
_TOURNAMENT_DIR = os.path.abspath(os.path.join(_PROJECT_ROOT, 'tournament'))
if _TOURNAMENT_DIR not in sys.path:
    sys.path.insert(0, _TOURNAMENT_DIR)

import importlib.util

# Attempt package-style import, fall back to loading by path if necessary
try:
    from tournament.connect4.connect_state import ConnectState  # type: ignore
except Exception:
    conn_path = os.path.join(_PROJECT_ROOT, "tournament", "connect4", "connect_state.py")
    spec = importlib.util.spec_from_file_location("connect_state", conn_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore
    ConnectState = getattr(mod, "ConnectState")


def play_single_game(a_cls, b_cls, params_a: Dict[str, Any] | None, params_b: Dict[str, Any] | None, rng_first: np.random.Generator) -> tuple[int, int]:
    """Play one game between a and b.

    Returns
    -------
    winner: int
        1 if a wins, -1 if b wins, 0 draw
    moves: int
        Number of moves played in the game
    """
    a = a_cls()
    b = b_cls()
    # apply parameter overrides to instances
    if params_a:
        for k, v in params_a.items():
            setattr(a, k, v)
    if params_b:
        for k, v in params_b.items():
            setattr(b, k, v)
    a.mount()
    b.mount()

    # decide who is first
    if rng_first.random() < 0.5:
        first, second = a, b
        first_name = "a"
    else:
        first, second = b, a
        first_name = "b"

    state = ConnectState()
    moves = 0
    while not state.is_final():
        current = first if state.player == -1 else second
        try:
            action = int(current.act(state.board))
        except Exception:
            # if policy fails, pick a random legal move
            rng = np.random.default_rng()
            avail = state.get_free_cols()
            action = int(rng.choice(avail))
        state = state.transition(action)
        moves += 1

    winner = state.get_winner()
    if winner == -1:
        # -1 corresponds to the player that moves when state.player == -1
        return (1 if first_name == "a" else -1, moves)
    elif winner == 1:
        return (-1 if first_name == "a" else 1, moves)
    else:
        return (0, moves)


def run_series(args):
    """Worker to run a chunk of games. args is a tuple packed for Pool."""
    (
        a_spec,
        b_spec,
        params_a,
        params_b,
        n_games,
        seed,
    ) = args
    rng = np.random.default_rng(seed)

    # a_spec / b_spec can be either a class object or a tuple (file_path, class_name)
    def _load_class(spec):
        if isinstance(spec, tuple):
            file_path, class_name = spec
            sp = importlib.util.spec_from_file_location(class_name, file_path)
            mod = importlib.util.module_from_spec(sp)
            assert sp and sp.loader
            sp.loader.exec_module(mod)  # type: ignore
            return getattr(mod, class_name)
        # assume it's a class
        return spec

    AClass = _load_class(a_spec)
    BClass = _load_class(b_spec)

    wins_a = 0
    wins_b = 0
    draws = 0
    total_moves = 0
    for i in range(n_games):
        w, moves = play_single_game(AClass, BClass, params_a, params_b, rng)
        total_moves += moves
        if w == 1:
            wins_a += 1
        elif w == -1:
            wins_b += 1
        else:
            draws += 1
    avg_moves = total_moves / max(1, n_games)
    # include per-chunk counts for variance estimation
    return {"wins_a": wins_a, "wins_b": wins_b, "draws": draws, "games": n_games, "avg_moves": avg_moves}


def param_grid_search(
    a_cls,
    b_cls,
    grid: Dict[str, Iterable],
    n_games_per_combo: int = 200,
    processes: int = 4,
    chunk_size: int = 50,
    output_dir: str = "experiments/results",
):
    """Run grid search over provided parameter grid for the agent `a_cls`.

    grid: mapping param_name -> iterable of values. Only applied to `a_cls`.
    `b_cls` is typically a random agent or same class for self-play.
    Results are written incrementally to `experiments/results/`.
    """
    os.makedirs(output_dir, exist_ok=True)
    keys = list(grid.keys())
    combos = list(itertools.product(*(grid[k] for k in keys)))

    results = []

    use_pool = processes and processes > 1
    pool = Pool(processes=processes) if use_pool else None

    for idx, combo in enumerate(combos, start=1):
        params = dict(zip(keys, combo))
        # split games into chunks so we can parallelize reproducibly
        chunk = chunk_size
        chunks = []
        full_chunks = n_games_per_combo // chunk
        # Resolve specs for multiprocessing: avoid passing class objects to pool
        def _to_spec(obj):
            # if already a tuple (path, name), return it
            if isinstance(obj, tuple):
                return obj
            # force classes to (file_path, class_name)
            if isinstance(obj, type):
                try:
                    return (os.path.abspath(inspect.getfile(obj)), obj.__name__)
                except Exception:
                    pass
            # if it's a class, attempt to find module file
            if hasattr(obj, "__module__"):
                modname = obj.__module__
                mod = sys.modules.get(modname)
                if mod is not None and hasattr(mod, "__file__"):
                    return (os.path.abspath(mod.__file__), obj.__name__)
            # fallback for dynamically-loaded classes not registered in sys.modules
            try:
                return (os.path.abspath(inspect.getfile(obj)), obj.__name__)
            except Exception:
                pass
            # fallback: return as-is (may be class)
            return obj

        a_spec = _to_spec(a_cls)
        b_spec = _to_spec(b_cls)
        for i in range(full_chunks):
            chunks.append((a_spec, b_spec, params, None, chunk, 1000 + i))
        rem = n_games_per_combo % chunk
        if rem:
            chunks.append((a_spec, b_spec, params, None, rem, 2000))

        if use_pool:
            res_chunks = pool.map(run_series, chunks)
        else:
            # run sequentially in current process to avoid pickling issues
            res_chunks = [run_series(c) for c in chunks]
        # Ensure project root is on sys.path when running scripts from the experiments/ folder
        _THIS_DIR = os.path.dirname(__file__)
        _PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))
        if _PROJECT_ROOT not in sys.path:
            sys.path.insert(0, _PROJECT_ROOT)

        # Also ensure `tournament/` is on sys.path so imports like `import connect4.*` work
        _TOURNAMENT_DIR = os.path.abspath(os.path.join(_PROJECT_ROOT, "tournament"))
        if _TOURNAMENT_DIR not in sys.path:
            sys.path.insert(0, _TOURNAMENT_DIR)

        agg = {"wins_a": 0, "wins_b": 0, "draws": 0, "games": 0, "avg_moves": 0.0}

        # aggregate counts and weighted avg of moves
        total_moves = 0.0
        total_games = 0
        for r in res_chunks:
            for k in ["wins_a", "wins_b", "draws", "games"]:
                agg[k] += r[k]
            total_moves += r.get("avg_moves", 0.0) * r.get("games", 0)
            total_games += r.get("games", 0)
        agg["avg_moves"] = total_moves / max(1, total_games)
        agg["params"] = params
        agg["win_rate_a"] = agg["wins_a"] / max(1, agg["games"])
        agg["win_rate_b"] = agg["wins_b"] / max(1, agg["games"])
        # per-chunk win rates for variance/violin plots
        try:
            agg["chunk_win_rates"] = [r["wins_a"] / max(1, r.get("games", 1)) for r in res_chunks]
        except Exception:
            agg["chunk_win_rates"] = []
        agg["timestamp"] = datetime.utcnow().isoformat()
        results.append(agg)
        # save incremental
        fname = os.path.join(output_dir, f"result_{idx}.json")
        with open(fname, "w", encoding="utf8") as f:
            json.dump(agg, f, indent=2)

    if pool is not None:
        pool.close()
        pool.join()
    # dump all results
    with open(os.path.join(output_dir, "all_results.json"), "w", encoding="utf8") as f:
        json.dump(results, f, indent=2)

    print(f"Saved {len(results)} results to {output_dir}")
