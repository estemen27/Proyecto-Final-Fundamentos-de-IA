"""Run a small pilot to validate experiments pipeline (fast)."""
import os
import sys
import importlib.util

# Ensure project root on sys.path
_THIS_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from run_experiments import param_grid_search  # type: ignore
from configs import PILOT


def import_policy(path_parts, symbol_name: str):
    path = os.path.join(*path_parts)
    spec = importlib.util.spec_from_file_location(symbol_name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore
    return getattr(mod, symbol_name)


def main():
    SantiPolicy = import_policy(["tournament", "groups", "Group Santi", "policy.py"], "SantiPolicy")
    Aha = import_policy(["tournament", "groups", "Group A", "policy.py"], "Aha")

    print('Pilot: self-play')
    param_grid_search(SantiPolicy, SantiPolicy, PILOT.grid, n_games_per_combo=PILOT.n_games_per_combo, processes=1, chunk_size=PILOT.chunk_size)
    print('Pilot: vs random')
    param_grid_search(SantiPolicy, Aha, PILOT.grid, n_games_per_combo=PILOT.n_games_per_combo, processes=1, chunk_size=PILOT.chunk_size)


if __name__ == '__main__':
    main()
