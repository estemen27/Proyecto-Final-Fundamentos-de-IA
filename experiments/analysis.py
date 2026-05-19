"""Generador de gráficas a partir de los JSON resultantes de `run_experiments`.

Diseñado para ejecutarse con `python experiments/analysis.py` sin Jupyter.
Genera PNGs en `experiments/results/figures/`.
"""
from __future__ import annotations

import json
import os
import math
import argparse
from typing import List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from math import sqrt


def _load_single_dir(results_dir: str, dataset_name: str) -> list[dict]:
    path_all = os.path.join(results_dir, "all_results.json")
    data = []
    if os.path.exists(path_all):
        with open(path_all, "r", encoding="utf8") as f:
            data = json.load(f)
    else:
        # collect individual JSONs
        for fname in sorted(os.listdir(results_dir)):
            if not fname.endswith('.json'):
                continue
            full = os.path.join(results_dir, fname)
            with open(full, 'r', encoding='utf8') as f:
                try:
                    data.append(json.load(f))
                except Exception:
                    continue

    rows = []
    for d in data:
        row = dict(d)
        params = row.pop('params', {}) if 'params' in row else {}
        for k, v in params.items():
            row[k] = v
        row['dataset'] = dataset_name
        rows.append(row)
    return rows


def load_results(results_dir: str = "experiments/results", dataset_filter: str = "all") -> pd.DataFrame:
    rows = []

    # Multi-dataset layout: experiments/results/self_play and experiments/results/vs_random
    self_play_dir = os.path.join(results_dir, "self_play")
    vs_random_dir = os.path.join(results_dir, "vs_random")
    has_multi_layout = os.path.isdir(self_play_dir) or os.path.isdir(vs_random_dir)

    if has_multi_layout:
        if dataset_filter in ("all", "self_play") and os.path.isdir(self_play_dir):
            rows.extend(_load_single_dir(self_play_dir, "self_play"))
        if dataset_filter in ("all", "vs_random") and os.path.isdir(vs_random_dir):
            rows.extend(_load_single_dir(vs_random_dir, "vs_random"))
    else:
        rows.extend(_load_single_dir(results_dir, "single"))

    df = pd.DataFrame(rows)
    return df


def ensure_dir(p: str):
    if not os.path.exists(p):
        os.makedirs(p, exist_ok=True)


def plot_line_by_param(df: pd.DataFrame, param: str, out_dir: str):
    plt.figure(figsize=(8, 5))
    if df[param].dtype == object:
        grouped = df.groupby(param)['win_rate_a'].mean().reset_index()
        plt.plot(grouped[param], grouped['win_rate_a'], marker='o')
    else:
        df_sorted = df.sort_values(param)
        plt.plot(df_sorted[param], df_sorted['win_rate_a'], marker='o', linestyle='-')
    plt.xlabel(param)
    plt.ylabel('win_rate_a')
    plt.title(f'Win rate vs {param}')
    plt.grid(True)
    fname = os.path.join(out_dir, f'line_{param}.png')
    plt.tight_layout()
    plt.savefig(fname)
    plt.close()


def plot_heatmap(df: pd.DataFrame, x: str, y: str, out_dir: str):
    pivot = df.pivot_table(values='win_rate_a', index=y, columns=x)
    plt.figure(figsize=(6, 4))
    plt.imshow(pivot.values, aspect='auto', cmap='viridis')
    plt.colorbar(label='win_rate_a')
    plt.xticks(ticks=np.arange(pivot.shape[1]), labels=[str(c) for c in pivot.columns], rotation=45)
    plt.yticks(ticks=np.arange(pivot.shape[0]), labels=[str(i) for i in pivot.index])
    plt.title(f'Heatmap win_rate_a ({y} x {x})')
    plt.tight_layout()
    fname = os.path.join(out_dir, f'heatmap_{x}_by_{y}.png')
    plt.savefig(fname)
    plt.close()


def plot_scatter(df: pd.DataFrame, x: str, out_dir: str):
    plt.figure(figsize=(8, 5))
    plt.scatter(df[x], df['win_rate_a'], c='C0')
    plt.xlabel(x)
    plt.ylabel('win_rate_a')
    plt.title(f'Scatter: {x} vs win_rate_a')
    plt.grid(True)
    fname = os.path.join(out_dir, f'scatter_{x}.png')
    plt.tight_layout()
    plt.savefig(fname)
    plt.close()


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for binomial proportion."""
    if n == 0:
        return 0.0, 1.0
    phat = k / n
    denom = 1 + (z * z) / n
    centre = (phat + (z * z) / (2 * n)) / denom
    half = (z * ((phat * (1 - phat) / n) + (z * z) / (4 * n * n)) ** 0.5) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def plot_param_with_ci(df: pd.DataFrame, param: str, out_dir: str):
    # Group by param value and compute mean win_rate and CI across combos
    groups = []
    xvals = []
    means = []
    lower = []
    upper = []
    for val, sub in df.groupby(param):
        xvals.append(val)
        mean = sub['win_rate_a'].mean()
        means.append(mean)
        # compute CI from aggregated wins/games across combos
        tot_wins = int(sub['wins_a'].sum())
        tot_games = int(sub['games'].sum())
        lo, hi = wilson_ci(tot_wins, tot_games)
        lower.append(lo)
        upper.append(hi)

    # sort by x
    order = sorted(range(len(xvals)), key=lambda i: xvals[i])
    x_sorted = [xvals[i] for i in order]
    means_sorted = [means[i] for i in order]
    lower_sorted = [lower[i] for i in order]
    upper_sorted = [upper[i] for i in order]

    plt.figure(figsize=(8, 5))
    plt.plot(x_sorted, means_sorted, marker='o')
    plt.fill_between(x_sorted, lower_sorted, upper_sorted, alpha=0.2)
    plt.xlabel(param)
    plt.ylabel('win_rate_a')
    plt.title(f'Win rate vs {param} with 95% CI (Wilson)')
    plt.grid(True)
    fname = os.path.join(out_dir, f'line_ci_{param}.png')
    plt.tight_layout()
    plt.savefig(fname, dpi=200)
    plt.savefig(os.path.join(out_dir, f'line_ci_{param}.svg'))
    plt.close()


def plot_violin_by_param(df: pd.DataFrame, param: str, out_dir: str):
    # requires chunk_win_rates in rows
    if 'chunk_win_rates' not in df.columns:
        return
    vals = []
    labels = []
    for val, sub in df.groupby(param):
        # flatten chunk lists
        arr = []
        for lst in sub['chunk_win_rates'].dropna():
            try:
                arr.extend(list(lst))
            except Exception:
                pass
        if not arr:
            continue
        vals.append(arr)
        labels.append(str(val))

    if not vals:
        return
    plt.figure(figsize=(max(6, len(vals) * 0.7), 5))
    plt.violinplot(vals, showmeans=True)
    plt.xticks(ticks=range(1, len(labels) + 1), labels=labels, rotation=45)
    plt.ylabel('chunk win rate (a)')
    plt.title(f'Violin of chunk win rates by {param}')
    plt.tight_layout()
    fname = os.path.join(out_dir, f'violin_{param}.png')
    plt.savefig(fname, dpi=200)
    plt.savefig(os.path.join(out_dir, f'violin_{param}.svg'))
    plt.close()


def estimate_linear_importance(df: pd.DataFrame, param_cols: List[str]) -> pd.Series:
    # Build X matrix and standardize
    X = df[param_cols].astype(float).to_numpy()
    # handle constant columns
    X_std = np.std(X, axis=0, ddof=0)
    X_centered = X - np.mean(X, axis=0)
    # avoid divide by zero
    nonzero = X_std != 0
    X_standard = X_centered.copy()
    X_standard[:, nonzero] = X_centered[:, nonzero] / X_std[nonzero]
    y = df['win_rate_a'].to_numpy()
    # solve least squares
    coef, *_ = np.linalg.lstsq(X_standard, y, rcond=None)
    coef_series = pd.Series(coef, index=param_cols)
    return coef_series.abs().sort_values(ascending=False)


def main():
    parser = argparse.ArgumentParser(description="Generate plots for experiment results")
    parser.add_argument("--results-dir", default=os.path.join('experiments', 'results'))
    parser.add_argument("--dataset", default="all", choices=["all", "self_play", "vs_random"])
    args = parser.parse_args()

    results_dir = args.results_dir
    out_dir = os.path.join(results_dir, 'figures' if args.dataset == 'all' else f'figures_{args.dataset}')
    ensure_dir(out_dir)

    df = load_results(results_dir, dataset_filter=args.dataset)
    if df.empty:
        print('No results found in', results_dir)
        return

    # Show a small summary
    print('Loaded', len(df), 'result rows')

    # Find parameter columns (non-metric)
    metric_cols = {'wins_a', 'wins_b', 'draws', 'games', 'win_rate_a', 'win_rate_b', 'timestamp', 'avg_moves', 'params', 'chunk_win_rates'}
    param_cols = [c for c in df.columns if c not in metric_cols]
    numeric_params = [c for c in param_cols if pd.api.types.is_numeric_dtype(df[c])]

    # Line plots per parameter
    for p in param_cols:
        try:
            plot_line_by_param(df, p, out_dir)
        except Exception as e:
            print('Skipping line plot for', p, 'error:', e)

    # Line + CI and violin plots per parameter
    for p in param_cols:
        try:
            plot_param_with_ci(df, p, out_dir)
        except Exception as e:
            print('Skipping CI line for', p, 'error:', e)
        try:
            plot_violin_by_param(df, p, out_dir)
        except Exception as e:
            print('Skipping violin for', p, 'error:', e)

    # Heatmap for top two numeric params
    if len(numeric_params) >= 2:
        x, y = numeric_params[0], numeric_params[1]
        try:
            plot_heatmap(df, x, y, out_dir)
        except Exception as e:
            print('Skipping heatmap:', e)

    # Scatter plots
    for p in numeric_params:
        try:
            plot_scatter(df, p, out_dir)
        except Exception as e:
            print('Skipping scatter for', p, 'error:', e)

    # Importance via linear regression coefficients
    if numeric_params:
        try:
            importance = estimate_linear_importance(df, numeric_params)
            plt.figure(figsize=(8, 4))
            importance.plot(kind='bar')
            plt.ylabel('abs(standardized coef)')
            plt.title('Estimated parameter importance (linear)')
            plt.tight_layout()
            plt.savefig(os.path.join(out_dir, 'param_importance_linear.png'))
            plt.close()
            print('Parameter importance:')
            print(importance)
        except Exception as e:
            print('Could not compute importance:', e)

    # Histogram of avg_moves
    if 'avg_moves' in df.columns:
        try:
            plt.figure(figsize=(8, 4))
            plt.hist(df['avg_moves'].dropna(), bins=20)
            plt.xlabel('avg_moves')
            plt.ylabel('count')
            plt.title('Distribution of average game length (per combo)')
            plt.tight_layout()
            plt.savefig(os.path.join(out_dir, 'hist_avg_moves.png'))
            plt.close()
        except Exception as e:
            print('Skipping avg_moves histogram:', e)

    print('Saved figures to', out_dir)


if __name__ == '__main__':
    main()
