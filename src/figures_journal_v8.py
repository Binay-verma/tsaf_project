"""New figures for journal draft v8, drawn only from committed analysis files.

Figure 4: change in lead-1 event MASE relative to calendar for the Ziel designs (local models), India vs NYC.
Figure 5: India 2025 regret versus the hindsight-better representation: follow-2024 rule vs equal-weight combination.
Run from the repository root: python src/figures_journal_v8.py <output dir>
"""
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MaxNLocator

ROOT = Path(__file__).resolve().parents[1]
INK, INK2, GRID, SURFACE = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
S1, S2, S3 = '#2a78d6', '#eb6834', '#1baf7a'
NAMES = {'ridge': 'Rich Ridge', 'sarimax': 'SARIMAX', 'lightgbm': 'Stable LightGBM', 'lightgbm_capacity2': 'Tree leaf min. 2',
         'chronos': 'Chronos-2', 'timesfm': 'TimesFM-3'}
LOCAL = ['ridge', 'sarimax', 'lightgbm', 'lightgbm_capacity2']


def style(ax):
    ax.set_facecolor(SURFACE)
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)
    for s in ['left', 'bottom']:
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(axis='x', color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.axvline(0, color=INK2, linewidth=0.8)
    ax.xaxis.set_major_locator(MaxNLocator(4))


def figure4(out):
    i = pd.concat([pd.read_csv(ROOT/'results/ziel_replacing_v1/analysis/event_window_balanced.csv'),
                   pd.read_csv(ROOT/'results/ziel_replacing_v2/analysis/event_window_balanced.csv')]).drop_duplicates(['model', 'arm', 'horizon'])
    n = pd.read_csv(ROOT/'results/ziel_nyc_v1/analysis/event_window_balanced.csv')
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    fig.patch.set_facecolor(SURFACE)
    designs = [('sunday_day', 'hSun', S1, 'o'), ('replace_pooled', 'Rph', S2, 's'), ('replace_typed', 'RpH', S3, 'D')]
    for ax, (title, b, h) in zip(axes, [('India festival windows, lead 1', i, 1), ('NYC observance windows, decision lead 1', n, 8)]):
        style(ax)
        m = b[b.horizon.eq(h)].pivot(index='model', columns='arm', values='MASE')
        for k, (arm, label, colour, marker) in enumerate(designs):
            y = [j+(k-1)*0.22 for j in range(len(LOCAL))]
            x = [m.loc[mo, arm]-m.loc[mo, 'calendar'] for mo in LOCAL]
            ax.scatter(x, y, s=34, color=colour, marker=marker, edgecolor=SURFACE, linewidth=1.5, label=label, zorder=3)
        ax.set_yticks(range(len(LOCAL))); ax.set_yticklabels([NAMES[mo] for mo in LOCAL], color=INK)
        ax.invert_yaxis()
        ax.set_title(title, fontsize=9, color=INK, loc='left')
        ax.set_xlabel('MASE minus calendar MASE (negative = better)', fontsize=8, color=INK2)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=8, loc='upper center', ncol=3, labelcolor=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    for ext in ['png', 'pdf']:
        fig.savefig(out/f'ziel_designs.{ext}', dpi=200, facecolor=SURFACE)
    plt.close(fig)


def figure5(out):
    d = pd.read_csv(ROOT/'results/representation_combination_v2/analysis/india_2025_decision_rules.csv')
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.6), sharey=True)
    fig.patch.set_facecolor(SURFACE)
    order = [(mo, rep) for mo in ['ridge', 'sarimax', 'lightgbm', 'lightgbm_capacity2', 'chronos', 'timesfm'] for rep in ['day', 'window']]
    for ax, h in zip(axes, [1, 7, 14]):
        style(ax)
        x = d[d.horizon.eq(h)].set_index(['model', 'representation'])
        for j, key in enumerate(order):
            f, c = x.loc[key, 'follow_regret'], x.loc[key, 'combine_regret']
            ax.plot([f, c], [j, j], color=GRID, linewidth=1.2, zorder=1)
        ax.scatter([x.loc[k, 'follow_regret'] for k in order], range(len(order)), s=30, color=S1, marker='o',
                   edgecolor=SURFACE, linewidth=1.5, label='Use 2024 winner', zorder=3)
        ax.scatter([x.loc[k, 'combine_regret'] for k in order], range(len(order)), s=30, color=S2, marker='s',
                   edgecolor=SURFACE, linewidth=1.5, label='Average typed and pooled', zorder=3)
        ax.set_title(f'Lead {h}', fontsize=9, color=INK, loc='left')
        ax.set_yticks(range(len(order))); ax.set_yticklabels([f'{NAMES[m]} ({r})' for m, r in order], color=INK, fontsize=7.5)
        ax.invert_yaxis()
    axes[1].set_xlabel('2025 regret: MASE minus the hindsight-better representation', fontsize=8, color=INK2)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=8, loc='upper center', ncol=2, labelcolor=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    for ext in ['png', 'pdf']:
        fig.savefig(out/f'decision_rules.{ext}', dpi=200, facecolor=SURFACE)
    plt.close(fig)


if __name__ == '__main__':
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    figure4(out); figure5(out)
    print('ok')
