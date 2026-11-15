"""Figures for journal v13 (shrinkage across stages, per-state forest, leaf size and window). Writes manuscript/journal_v13_src/figures/."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import scorecard_v1 as sc  # noqa: E402

OUT = ROOT/'manuscript/journal_v13_src/figures'
BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK,
                     'xtick.color': MUTED, 'ytick.color': MUTED, 'axes.spines.top': False, 'axes.spines.right': False})


def ci(base, cohort, model, fm=False):
    u = sc.fm(base, model) if fm else sc.load(base, cohort, model)
    return sc.tint(u.groupby(['family', 'year'])['diff'].mean().values)


def shrinkage():
    panels = [('SARIMAX', [('Stage A', ci('results/longer_panel_stage_a_v1', 'event_window', 'sarimax')),
                           ('Stage B', ci('results/longer_panel_stage_b_v1', 'event_window', 'sarimax')),
                           ('First test', ci('results/new_states_v1', 'event_window', 'sarimax')),
                           ('Second test', ci('results/new_states_v2', 'event_window', 'sarimax'))]),
              ('Leaf-2 LightGBM', [('Stage A', ci('results/longer_panel_stage_a_v1', 'event_window', 'lightgbm_capacity2')),
                                   ('Stage B', ci('results/longer_panel_stage_b_v1', 'event_window', 'lightgbm_capacity2')),
                                   ('First test', ci('results/new_states_v1', 'event_window', 'lightgbm_capacity2')),
                                   ('Second test', ci('results/new_states_v2', 'event_window', 'lightgbm_capacity2'))]),
              ('TimesFM-3', [('Stage A', (0.0506, np.nan, np.nan)), ('First test', ci('results/new_states_v1', None, 'timesfm', fm=True))])]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6), sharey=True)
    for ax, (name, pts) in zip(axes, panels):
        xs = np.arange(len(pts))
        for x, (lab, (m, lo, hi)) in zip(xs, pts):
            if np.isfinite(lo):
                ax.plot([x, x], [lo, hi], color=BLUE, lw=2, solid_capstyle='round')
            ax.plot(x, m, 'o', ms=6, color=BLUE if np.isfinite(lo) else 'white', mec=BLUE, mew=2, zorder=3)
        ax.axhline(0, color=MUTED, lw=1)
        ax.set_xticks(xs); ax.set_xticklabels([p[0] for p in pts], rotation=30, ha='right')
        ax.set_title(name, fontsize=9, color=INK, loc='left')
        ax.grid(axis='y', color=GRID, lw=0.8); ax.set_axisbelow(True)
    axes[0].set_ylabel('Typed − pooled MASE\n(positive favours pooled)')
    fig.tight_layout(); fig.savefig(OUT/'shrinkage.png', dpi=300); plt.close(fig)


def forest():
    f = pd.read_csv(ROOT/'results/scorecard_v1/forest_by_state.csv')
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 4.0), sharey=True)
    order = (f[f.model == 'lightgbm_capacity2'].sort_values(['test', 'state'], ascending=[False, False]))
    states = list(order.state)
    for ax, (model, title) in zip(axes, [('sarimax', 'SARIMAX'), ('lightgbm_capacity2', 'Leaf-2 LightGBM')]):
        g = f[f.model == model].set_index('state').loc[states].reset_index()
        for i, r in g.iterrows():
            col = BLUE if r.test == 'First test' else ORANGE
            ax.plot([r.ci_low, r.ci_high], [i, i], color=col, lw=2, solid_capstyle='round')
            ax.plot(r.estimate, i, 'o' if r.test == 'First test' else 's', ms=6, color=col, mec='white', mew=1, zorder=3)
        ax.axvline(0, color=MUTED, lw=1)
        ax.set_yticks(range(len(states))); ax.set_yticklabels(states)
        ax.set_title(title, fontsize=9, color=INK, loc='left'); ax.set_xlabel('Typed − pooled MASE')
        ax.grid(axis='x', color=GRID, lw=0.8); ax.set_axisbelow(True)
    h = [plt.Line2D([], [], color=BLUE, marker='o', lw=2, label='First test'), plt.Line2D([], [], color=ORANGE, marker='s', lw=2, label='Second test')]
    fig.legend(handles=h, loc='lower center', ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.06, 1, 1)); fig.savefig(OUT/'forest.png', dpi=300); plt.close(fig)


def leaf_window():
    b = pd.read_csv(ROOT/'results/leaf_size_experiment_v1/analysis/by_leaf.csv')
    w = pd.read_csv(ROOT/'results/robustness_experiments_v1/analysis/window.csv')
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))
    ax = axes[0]
    for t, col, mk, lab in [('v1', BLUE, 'o', 'First test'), ('v2', ORANGE, 's', 'Second test')]:
        g = b[b.test == t].sort_values('leaf')
        ax.plot(g.leaf, g.typed_minus_pooled, color=col, lw=2, marker=mk, ms=6, mec='white', label=lab)
    ax.axhline(0, color=MUTED, lw=1); ax.set_xscale('log'); ax.set_xticks([1, 2, 3, 5, 10, 20]); ax.set_xticklabels(['1', '2', '3', '5', '10', '20'])
    ax.set_xlabel('Minimum leaf size L (730-day window)'); ax.set_ylabel('Typed − pooled MASE'); ax.set_title('LightGBM, leaf size', fontsize=9, loc='left')
    ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True); ax.legend(frameon=False)
    ax = axes[1]
    for (t, m), col, mk, ls in [(('v1', 'lgbm_leaf2'), BLUE, 'o', '-'), (('v2', 'lgbm_leaf2'), ORANGE, 's', '-'),
                                (('v1', 'lgbm_selected'), BLUE, 'o', '--'), (('v2', 'lgbm_selected'), ORANGE, 's', '--')]:
        g = w[(w.test == t) & (w.model == m)].sort_values('W')
        ax.plot(g.W/365, g.typed_minus_pooled, color=col, lw=2, ls=ls, marker=mk, ms=6, mec='white')
    ax.axhline(0, color=MUTED, lw=1); ax.set_xticks([2, 4, 6]); ax.set_xlabel('Training window (years)')
    ax.set_title('LightGBM, training window', fontsize=9, loc='left'); ax.grid(color=GRID, lw=0.8); ax.set_axisbelow(True)
    h = [plt.Line2D([], [], color=MUTED, lw=2, ls='-', label='leaf 2'), plt.Line2D([], [], color=MUTED, lw=2, ls='--', label='tuned leaf')]
    ax.legend(handles=h, frameon=False)
    fig.tight_layout(); fig.savefig(OUT/'leaf_window.png', dpi=300); plt.close(fig)


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    shrinkage(); forest()
    if (ROOT/'results/robustness_experiments_v1/analysis/window.csv').exists():
        leaf_window()
