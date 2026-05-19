"""Ejemplo sencillo para ejecutar el barrido de parámetros sobre `SantiPolicy`.

Ejecutar desde la raíz del repo:
    python experiments/run_santi_example.py
"""
import os
import sys
import importlib.util

# Ensure project root available when executing from experiments/
_THIS_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from run_experiments import param_grid_search  # type: ignore
from configs import PILOT, EXPLORATORY, PRODUCTION


def import_policy(path_parts, symbol_name: str):
    path = os.path.join(*path_parts)
    spec = importlib.util.spec_from_file_location(symbol_name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore
    return getattr(mod, symbol_name)


if __name__ == "__main__":
    # Use file specs for multiprocessing safety: (file_path, class_name)
    santi_spec = (
        os.path.join(_PROJECT_ROOT, "tournament", "groups", "Group Santi", "policy.py"),
        "SantiPolicy",
    )
    aha_spec = (
        os.path.join(_PROJECT_ROOT, "tournament", "groups", "Group A", "policy.py"),
        "Aha",
    )

    # Choose a preset: PILOT, EXPLORATORY, or PRODUCTION
    preset = PRODUCTION

    # If preset.processes is None, use CPU count - 1
    cpu_count = os.cpu_count() or 4
    processes = preset.processes if preset.processes is not None else max(1, cpu_count - 1)
    base_results = os.path.join(_PROJECT_ROOT, "experiments", "results")
    self_play_dir = os.path.join(base_results, "self_play")
    vs_random_dir = os.path.join(base_results, "vs_random")

    # 1) Self-play: compare different presets/parameters against same policy
    print('Running self-play grid (Santi vs Santi) with preset:', preset)
    param_grid_search(
        santi_spec,
        santi_spec,
        preset.grid,
        n_games_per_combo=preset.n_games_per_combo,
        processes=processes,
        chunk_size=preset.chunk_size,
        output_dir=self_play_dir,
    )

    # 2) vs random: measure robustness against random opponent
    print('Running robustness grid (Santi vs Aha random) with preset:', preset)
    param_grid_search(
        santi_spec,
        aha_spec,
        preset.grid,
        n_games_per_combo=preset.n_games_per_combo,
        processes=processes,
        chunk_size=preset.chunk_size,
        output_dir=vs_random_dir,
    )

