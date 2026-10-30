"""Render phase-two evidence without modifying forecasts or original results."""
from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from forecasting import ROOT


def table(frame):
    d = frame.copy()
    for col in d.select_dtypes('number'):
        d[col] = d[col].map(lambda x: f'{x:.4f}')
    return ('| '+' | '.join(map(str, d.columns))+' |\n| '+
            ' | '.join(['---']*len(d.columns))+' |\n'+
            '\n'.join('| '+' | '.join(map(str, row))+' |' for row in d.to_numpy())+'\n')


def main():
    out = ROOT/'results/strong_refit_v1'
    run = json.loads((out/'run.json').read_text())
    m = pd.read_csv(out/'metrics_macro.csv')
    a = m[m.year.eq(2026) & m.scope.eq('all')].pivot(
        index=['model', 'mode', 'schedule'], columns='horizon', values='MASE').reset_index()
    text = f'''# Rich histories and annual/monthly refits v1

Completed exploratory comparison: {run['selection_fits']} validation fits, {run['selected']} chosen configurations,
{run['deployment_fits']} deployment fits and {run['rows']:,} forecasts. No failed fits.
All new configurations exactly match the historical Chronos history-only 8,937 state/origin/lead cases.
Data and original expanded results remain unchanged.

The protocol was recorded before these new results. All 2024–2026 outcomes were already development evidence.
Each state/year/mode/lead/model selects parameters using a chronological 180-day pre-year block,
with fitting targets strictly before validation origins. Parameters stay frozen for the entire evaluation year,
for both annual and monthly schedules. Deployment labels end before each refit date. Thus monthly versus annual
changes the refit schedule, not the annual hyperparameter budget. Rich history has 27 causal lag/rolling/trend
and target-aligned annual-lag features; calendar and regional modes add 13 and 20 known calendar channels.
LightGBM uses eight grid points; Ridge uses three alphas. This is a stronger explicit baseline budget,
not proof of the strongest attainable local forecast.

## Partial 2026 macro MASE

Lower is better. Every configuration has the same 288 origins per state/lead. Scores use identical fixed
pre-year scales; monthly retraining does not change the denominator. Leads are individual target days.

'''+table(a)+'''
For reference, matched history-only Chronos macro MASE is 0.4679 / 1.1629 / 1.3617 at leads 1/7/14.
These are descriptive deployment-policy comparisons, not architecture-isolated or significance claims.
Monthly rich-calendar Ridge improves over annual at all three 2026 leads (0.5416/1.3115/1.5098
versus 0.5954/1.4910/1.8358), but does not beat the recorded Chronos macro scores.
LightGBM still does not establish superiority, despite richer histories and monthly updates.

## Festival and refit failures of generalisation

Monthly refitting is not universally helpful. In 2024, regional Ridge lead-14 event MASE worsens from
1.347 to 1.731; in 2025, calendar LightGBM lead-14 event MASE worsens from 1.423 to 2.241.
Do not select a refit schedule on those event outcomes and present it as a clean test. The two event years
and three related states provide weak independent evidence; no row-level significance test is performed.
Full state/year and event/non-event metrics, selected parameters, all validation losses, deployment cutoffs,
runtime and source/code/protocol hashes are retained. No weather or real-time vintage reconstruction is claimed.

## Reproduce/audit

`.venv/bin/python src/test_robust_baselines.py` and `.venv/bin/python src/audit_phase2.py`.
The runner refuses to overwrite completed/interrupted fit artifacts; create a new versioned output/protocol
and use `--out` for a new run. Existing forecasts are not rewritten by this report generator.
'''
    (out/'REPORT.md').write_text(text)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, model in zip(axes, ['ridge', 'lightgbm']):
        g = m[m.model.eq(model) & m['mode'].eq('rich_calendar') & m.year.eq(2026) & m.scope.eq('all')]
        for schedule, h in g.groupby('schedule'):
            ax.plot(h.horizon, h.MASE, 'o-', label=schedule)
        ax.plot([1, 7, 14], [.467902, 1.162937, 1.361749], 'o--', label='cached Chronos history')
        ax.set_title(model+' / rich calendar'); ax.set_xticks([1, 7, 14]); ax.set_xlabel('Lead day'); ax.legend(fontsize=8)
    axes[0].set_ylabel('Macro MASE (lower better)')
    fig.suptitle('Partial 2026: matched cases, exploratory comparisons'); fig.tight_layout()
    fig.savefig(out/'refit_comparison.png', dpi=160); plt.close(fig)

    out = ROOT/'results/regional_transfer_v1'
    m = pd.read_csv(out/'metrics_macro.csv')
    a = m[m.scope.eq('all')].pivot(index=['year', 'mode', 'arm'], columns='horizon', values='MASE').reset_index()
    text = '''# Regional regression transfer v1

162 fixed Ridge fits, 53,622 predictions, six configurations, 8,937 matched cases each.
Alpha=10 is fixed, with no held-out-region tuning. All fitting labels predate each evaluation year.
Three arms share features and dates: target-region local fitting, pooled fitting including the target,
and regression fitting on the other two states only. Source-fitted StandardScaler and coefficients in
the last arm never use target-region rows. Tests explicitly perturb the held-out region and verify
source coefficients and scaler do not change; future-year perturbations cannot change fits/normalizers.

**This is not geographic cold start.** Target-region observed history and a fixed pre-year mean/std are
allowed context/normalization. Scaling parameters use only recorded values before the held-out year.
The sources and target are all from the same compilation; this is not independent dataset replication.
The forward-held-out year is never pooled into training. No future-year leave-one-year-out leakage is used.

## Equal-state macro MASE

'''+table(a)+'''
Held-out-region transfer generally degrades versus local fitting, particularly at long leads. For 2026
rich-calendar lead 14, leave-region-out is 2.3468 versus local 2.0879; pooled-all is 1.5266.
Pooling all regions can help but includes target-region fitting data, so it cannot be advertised as
successful transfer to a wholly unseen region. These negative transfer results are retained.

Three states and two historical event years do not support broad regional generalisation, causal festival
claims or high-precision significance inference. All current outcomes are exploratory. Full event/non-event,
state/year metrics and training state/cutoff/normalizer logs remain alongside this report.

Audit with `.venv/bin/python src/test_regional_transfer.py` and `src/audit_phase2.py`.
'''
    (out/'REPORT.md').write_text(text)

    out = ROOT/'results/second_model_audit_v1'
    info = json.loads((out/'fixture_run.json').read_text())
    text = '''# TimesFM 3.0 independent-model audit v1

## Identity, rights and exposure

- Official model: `google/timesfm-3.0-pytorch`, revision `43046b85ec22d584a13f8098c2ed39c889e129c2`.
- Code: Google Research TimesFM revision `e51928e27119cb17bebc005be2696b75e0a9e688`, package 3.0.2.
  Forty installed Python files match the pinned source bytes; installed hashes are recorded.
- Actual downloaded safetensors: 1,322,898,824 bytes; SHA-256
  `a7592b0a8432baee54483254e5647856911ce69e09d09a9bb65904b2d98f17da`.
- Earliest weight-upload commit `6455822fd4703713f3bf9cb2845f7ba51dc65250`,
  24 August 2026 22:41:42 UTC. Its LFS object equals evaluated weights; predecessor has no safetensors.
  This is upload chronology, not an exact training cutoff. Historical/proxy overlap remains unresolved.
- The model card lists GIFT-Eval pretraining excluding fev-bench overlap, Wikipedia and Google Trends,
  and synthetic/augmented data. It is not an exhaustive corpus identity or numeric deduplication audit.
- Source code is separately Apache-2.0; the downloadable model has TimesFM Non-Commercial License v1.0.
  Its text permits noncommercial academic research and prohibits distributing the model/derivatives.
  The weights and vendor installation are kept outside the Git checkout and are not pushed.
  Future commercial/production use is not covered by this research setup.

## Actual API validation

CPU, torch 2.15.0+cpu, context 730, horizon 14, batch 1, symmetry averaging off; independent cases.
18 predeclared tasks: three states, origins 1 September / 1 October 2026, history/calendar/regional modes.
252 forecast days and 2,268 native quantile values are saved. Future-known covariate arrays cover past730+
future14 without future target observations. Perturbing unseen target values leaves inputs unchanged.
All forecasts are finite, shapes match the documented API and no adjacent native quantile crossings occur.

These targets postdate unchanged weight upload, conditional on accurate source dates. They were already
historically inspected: **not an untouched confirmation**. The tiny fixture has no festival outcomes and
does not establish model superiority, a successful calendar method, or multi-model festival replication.
Native quantile metrics are descriptive fixture checks, not a calibrated uncertainty study.

## Remaining model work

Run the full matched calendar/feature-count/placebo experiment for both model families under a new
protocol and compute budget. Do not inherit Chronos exposure evidence or compare differing cases.
Any event-year before August 2026 remains overlap-uncertain for TimesFM. The frozen source ends before
2026 Diwali; no retrospective clean post-weight festival result can be manufactured.

## Reproduce

The audit evidence stores API commit/tree metadata, pinned model card/licence/config, downloaded-byte
hashes, installed-code hashes, package versions and the fixture protocol/tasks/results. To reproduce,
install the pinned Google source (outside this repo) plus torch 2.15.0+cpu, huggingface-hub 2.4.0 and
safetensors 0.8.0; download the exact HF revision with TLS enabled and verify the safetensors hash.
`src/timesfm_fixture.py` uses the local path recorded in `weight_download.json` and refuses overwrite.
For another machine, prepare a new audit directory and update that location explicitly; local model paths
and installed processes are not assumed to transfer automatically.
'''
    (out/'REPORT.md').write_text(text)
    print('Phase-two reports and figure written.')


if __name__ == '__main__':
    main()
