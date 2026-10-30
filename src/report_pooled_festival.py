"""Create a bounded current brief and standalone all-lead research figures."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pooled_festival_experiment import OUT, ROOT
from finalize_festival_features import MODELS
from report_multifestival import markdown

NAMES = ['Rich Ridge', 'Stable LightGBM', 'Tree leaf minimum 2', 'SARIMAX', 'Chronos-2', 'TimesFM-3']


def main():
    if (OUT/'summary_assets.json').exists():
        raise FileExistsError('Preserve completed brief/figures')
    for name in ['independent_audit.json', 'inputs_fits_audit.json', 'probabilistic_audit.json']:
        assert json.loads((OUT/name).read_text())['status'] == 'pass'
    metrics = {c: pd.read_csv(OUT/c/'primary_metrics_balanced.csv') for c in ['event', 'non_event']}
    contrasts = {c: pd.read_csv(OUT/c/'contrasts_balanced.csv') for c in metrics}
    columns = [('day5', h) for h in [1, 7, 14]]+[('window5', h) for h in [1, 7, 14]]
    arrays = {}
    for cohort, d in contrasts.items():
        a = np.zeros((6, 6))
        for i, model in enumerate(MODELS):
            for j, (arm, h) in enumerate(columns):
                row = d[d.model.eq(model) & d.arm.eq(arm) & d.reference.eq('pooled_day5' if arm == 'day5' else 'pooled_window5') & d.horizon.eq(h)]
                assert len(row) == 1
                a[i, j] = row.MASE_change.iloc[0]
        arrays[cohort] = a
    limit = max(abs(x).max() for x in arrays.values())
    limit = max(limit, .001)
    for cohort, a in arrays.items():
        fig, ax = plt.subplots(figsize=(12, 4.8))
        im = ax.imshow(a, cmap='RdBu_r', vmin=-limit, vmax=limit, aspect='auto')
        ax.set_yticks(range(6), NAMES, fontsize=11)
        ax.set_xticks(range(6), ['Day: lead 1', 'Day: lead 7', 'Day: lead 14', 'Window: lead 1', 'Window: lead 7', 'Window: lead 14'], fontsize=10)
        ax.axvline(2.5, color='white', linewidth=3)
        for i in range(6):
            for j in range(6):
                ax.text(j, i, f'{a[i,j]:+.3f}', ha='center', va='center', fontsize=12,
                    color='white' if abs(a[i,j]) > .65*limit else 'black')
        ax.set_title(('Festival anchors' if cohort == 'event' else 'Matched non-event targets')+' · typed minus pooled at five channels', fontsize=14, pad=16)
        fig.colorbar(im, ax=ax, label='MASE change: negative favours typed; positive favours pooled')
        fig.tight_layout()
        for ext in ['png', 'pdf']:
            fig.savefig(OUT/f'{cohort}_typed_minus_pooled5.{ext}', dpi=190)
        plt.close(fig)
    # Publish a complete next-day score table, not a model-winner shortlist.
    e = metrics['event']; table = e[e.horizon.eq(1)].pivot(index='model', columns='arm', values='MASE').reindex(index=MODELS,
        columns=['calendar', 'pooled_day1', 'pooled_day5', 'day5', 'pooled_window1', 'pooled_window5', 'window5', 'zero1'])
    table.to_csv(OUT/'next_day_all_models_arms.csv')
    fig, ax = plt.subplots(figsize=(13, 4.8))
    vmax = float(table.to_numpy().max())
    im = ax.imshow(table, aspect='auto', vmin=0, vmax=vmax, cmap='YlGnBu')
    ax.set_yticks(range(6), NAMES, fontsize=11)
    ax.set_xticks(range(8), ['Calendar', 'Pooled\nday 1ch', 'Pooled\nday 5ch', 'Typed\nday 5ch', 'Pooled\nwindow 1ch', 'Pooled\nwindow 5ch', 'Typed\nwindow 5ch', 'Zero\n1ch'], fontsize=10)
    for i in range(6):
        for j in range(8):
            v = table.iloc[i,j]
            ax.text(j, i, f'{v:.3f}', ha='center', va='center', fontsize=11, color='white' if v > .6*vmax else 'black')
    ax.set_title('Next-day festival-anchor MASE · all six variants and eight arms', fontsize=14, pad=15)
    fig.colorbar(im, ax=ax, label='MASE: lower is better'); fig.tight_layout()
    for ext in ['png', 'pdf']:
        fig.savefig(OUT/f'next_day_all_models_arms.{ext}', dpi=190)
    plt.close(fig)
    lines = ['# Do separate festival identities help beyond a pooled flag?', '',
        'Completed exploratory follow-up, 30 October 2026. Daily supplied electricity in Delhi, Karnataka and Maharashtra. Historical 2024–2025 labels were previously inspected; this is not a clean final test.', '',
        'The original study asked whether predictions differ during festivals. The preceding intervention added explicit festival features. This follow-up asks whether five separate family features add value beyond marking their pooled dates, and whether padding alone changes the forecast.', '',
        '## Next-day festival-anchor results', '',
        'MASE is scaled error; lower is better. Same 72 event/lead cases per arm, including 24 next-day cases, with equal states within year, years within family and families overall. Each tree capacity regime keeps its own fixed parameters and baseline.', '', markdown(table.round(5).reset_index()), '',
        '## Typed minus pooled at the same five-channel budget', '',
        'Negative changes favour separate family channels; positive changes favour the pooled representation. These are macro-MASE differences, not accuracy percentages. All leads and both representations are shown; no best arm is selected for future use.', '']
    for cohort, d in contrasts.items():
        selected = d[((d.arm.eq('day5') & d.reference.eq('pooled_day5')) | (d.arm.eq('window5') & d.reference.eq('pooled_window5')))]
        pivot = selected.pivot(index='model', columns=['arm', 'horizon'], values='MASE_change').reindex(index=MODELS)
        pivot.columns = [f'{a}: lead {h}' for a,h in pivot.columns]
        lines += ['### '+('Festival anchors' if cohort == 'event' else 'Matched non-event targets'), '', markdown(pivot.round(5).reset_index()), '']
    lines += ['## Native uncertainty', '',
        'Common native0.1–0.9quantiles and unmodified80%intervals are scored separately for both foundation models. Coverage accompanies width, scaled pinball and a one-interval WIS; these intervals have not been calibrated. See both NATIVE_UNCERTAINTY.md reports and the independent arithmetic audit. The limited historical cases cannot certify calibration.', '',
        '## Verification and limits', '',
        '4,320 new forecasts plus 2,592 hash-checked reused forecasts give 6,912 compared rows across two distinct72-case cohorts. Complete-case, label/scale/hierarchy/paired-score, actual-input-byte, budget/cutoff/support and probabilistic arithmetic audits are recorded. All original source/result/deck/future-freeze hashes in the protection manifest remain unchanged.', '',
        'The bounded separate clean scalar review reproduces all135checked forecasts within tolerance, maximum7.617e-12GWh, and every label vector exactly. Its strict overall status is discrepancies_retained: the Delhi tree matrices differ at one near-zero trend entry per checked block (maximum float32 difference1.421e-14GWh). The original failure and localization are retained; do not call this a full clean-room pass or assume float32 guarantees byte identity.', '',
        'Separate versus pooled channels changes statistical sharing and signal allocation. Same dimensions do not identify a causal festival-identity mechanism. State scopes differ; annual dates are not complete amendment histories; two years and related dates provide limited independent evidence. Source reuse/processing clarification, independent human review, historical/proxy exposure and untouched/source-independent confirmation remain open. Frozen future forecasts and the paused workflow are unchanged.', '',
        'Reproduction: [POOLED_FEATURE_REPRODUCTION.md](POOLED_FEATURE_REPRODUCTION.md). Full results: [event](results/pooled_festival_v1/event/REPORT.md), [non-event](results/pooled_festival_v1/non_event/REPORT.md).', '',
        'Later checkpoint: the supervised family-label exclusion study is completed and audited; see LABEL_TRANSFER_RESULTS_BRIEF.md. Target history remains allowed and longer-lead failures are retained. External rights/human and later prospective gates remain open.']
    (ROOT/'POOLED_FEATURE_RESULTS_BRIEF.md').write_text('\n'.join(lines)+'\n')
    (OUT/'README.md').write_text('# Pooled festival follow-up\n\nSee event/ and non_event/ REPORT.md and NATIVE_UNCERTAINTY.md. Root audit JSONs establish actual checks; clean_scalar_review.json deliberately retains its strict numerical discrepancy. Native quantiles and unsuccessful optimizer attempts are unchanged. Research figures show all variants/leads and preserve negative effects. No untouched/causal/universal superiority claim.\n')
    (OUT/'summary_assets.json').write_text(json.dumps(dict(status='completed', figure_scope='All6variants, all3leads, both encodings/cohorts; complete nextday8armtable', source='Audited saved aggregate tables only; no model reruns'), indent=2)+'\n')
    print('Created current brief and3standalone PNG/PDF figures')


if __name__ == '__main__':
    main()
