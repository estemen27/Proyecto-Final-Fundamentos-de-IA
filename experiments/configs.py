"""Experiment configuration presets and grids.

Edit these presets to change which parameters are swept and the number of games.
"""
from dataclasses import dataclass
from typing import Dict, Iterable


@dataclass
class ExperimentConfig:
    grid: Dict[str, Iterable]
    n_games_per_combo: int
    processes: int | None = None
    chunk_size: int = 50


# Small pilot grid (fast)
PILOT = ExperimentConfig(
    grid={
        "SAFETY_PENALTY": [2000.0, 8000.0],
        "THREAT_WEIGHT_3": [1.0, 5.0],
        "CENTER_WEIGHT": [1.0, 3.0],
    },
    n_games_per_combo=30,
    processes=1,
)

# Larger exploratory grid
EXPLORATORY = ExperimentConfig(
    grid={
        "SAFETY_PENALTY": [2000.0, 5000.0, 8000.0, 15000.0],
        "THREAT_WEIGHT_3": [1.0, 3.0, 5.0, 8.0],
        "CENTER_WEIGHT": [0.5, 1.0, 2.0, 3.0],
        "BLOCK_WEIGHT": [4000.0, 7000.0, 10000.0],
    },
    n_games_per_combo=200,
    processes=None,
)

# Full production grid (be careful: large)
PRODUCTION = ExperimentConfig(
    grid={
        "SAFETY_PENALTY": [2000.0, 5000.0, 8000.0, 15000.0, 20000.0],
        "THREAT_WEIGHT_3": [1.0, 3.0, 5.0, 8.0],
        "CENTER_WEIGHT": [0.5, 1.0, 2.0, 3.0, 4.0],
        "BLOCK_WEIGHT": [4000.0, 7000.0, 9000.0, 12000.0],
    },
    n_games_per_combo=500,
    processes=None,
)
