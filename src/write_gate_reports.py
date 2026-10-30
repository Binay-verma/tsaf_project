"""Reports from completed controls, versioned numerical fix and provenance work."""
from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from forecasting import ROOT


def table(frame):
    d=frame.copy()
    for col in d.select_dtypes('number'):
        d[col]=d[col].map(lambda x:f'{x:.4f}')
    return '| '+' | '.join(map(str,d.columns))+' |\n| '+' | '.join(['---']*len(d.columns))+' |\n'+''.join(
        '| '+' | '.join(map(str,row))+' |\n' for row in d.to_numpy())


def main():
    out=ROOT/'results/mechanism_controls_v1'
    parts=[]
    for model in ['chronos2','timesfm3']:
        a=pd.read_csv(out/model/'contrasts_two_year.csv');a['model']=model;parts.append(a)
    c=pd.concat(parts,ignore_index=True)
    c.to_csv(out/'contrasts_both_models.csv',index=False)
    report='''# Both-foundation-model mechanism controls v1

Completed:2304 fresh inference tasks,2700 scored predictions (150 identical event cases x9arms x2models),
2024–2025, three states, leads1/7/14. No old forecast cache was adopted as new evidence.
Models/code/weights are pinned; all cases and source/model/protocol hashes recorded. Each batch checks
that perturbing unseen targets cannot change constructed inputs. Zero native quantile crossings.
Original61 protected source/result files and frozen prospective predictions remain unchanged.

The protocol predates the new controls but follows historical result inspection. All outcomes exploratory,
with only two annual event clusters and one seeded placebo. No p-values, independent-day inference,
external preregistration, source-independence or causal provenance claim is made.

## Prespecified contrasts

Positive percentage = lower MAE for arm versus reference. Compute each state/year effect, average states
within year then years. These means are not ratios of the macro MASE table.

'''+table(c[['model','arm','reference','horizon','mean_state_improvement_pct']])+'''
## What changes the interpretation

1. Equal scalar dimensions give small/mixed regional increments: Chronos +0.22%/−0.68%/−0.81%,
TimesFM +1.17%/−0.09%/+2.12% at leads1/7/14. This does not demonstrate an encoding-independent regional benefit.
2. With seven channels held equal, regional increments are Chronos +1.43%/+1.59%/+1.55% and TimesFM
+4.72%/+3.25%/+6.43%. These differ markedly from the earlier ordinary-calendar-to-regional contrast,
which changes information and dimension together. Representation remains central to interpretation.
3. Zero channels change forecasts despite adding no event information. Seven zeros alter predictions by
up to6.05GWh (Chronos) and6.93GWh (TimesFM). Day1 mean error improvements from seven zeros are1.17% and1.99%.
Thus a small calendar gain alone cannot be assigned to extra date information without interface controls.
This is observed sensitivity, not proof of an implementation bug or a complete explanation of every gain.
4. Active placebo effects are model/lead dependent. Regional versus seven-channel placebo is negative
for Chronos day1 (−1.70%) but positive at its longer leads; TimesFM is positive across these tested leads.
One selected date-only seed is not an exchangeable randomisation distribution.
5. Delhi generic and regional inputs contain identical dates and produce identical predictions in both
dimensionalities, as expected. This check validates a specific implementation identity, not all calendar dates.

## Bounds

The scalar window discards relative-day detail. Scalar versus seven-channel results change both representation
and dimension; they do not isolate a pure dimension mechanism. Within each dimension, generic/regional
comparisons hold feature count fixed but change event information/duration. Annual dates are as-issued
evidence, not full amendment certification. Both historical years predate audited model uploads, so proxy/sample
overlap remains unresolved. No best arm, date shift or new forecast was selected from these outcomes.

Per-state/year metrics, individual-year contrasts and native predictions are retained under each model.
Audit using `src/audit_foundation_controls.py --model chronos2` and `--model timesfm3`.
'''
    (out/'REPORT.md').write_text(report)
    fig,axes=plt.subplots(1,3,figsize=(12,4),sharey=True)
    for ax,h in zip(axes,[1,7,14]):
        for model,g in c[c.horizon.eq(h)&c.arm.isin(['regional_window','regional_7'])].groupby('model'):
            vals=[g[g.arm.eq(a)].mean_state_improvement_pct.iloc[0] for a in ['regional_window','regional_7']]
            ax.plot([1,7],vals,'o-',label=model)
        ax.axhline(0,color='black',linestyle='--',linewidth=1);ax.set_xticks([1,7],['Scalar window','7 offsets'])
        ax.set_title(f'Lead {h}');ax.legend()
    axes[0].set_ylabel('Regional vs generic MAE reduction (%)');fig.suptitle('Equal-dimension contrasts; two exploratory event years')
    fig.tight_layout();fig.savefig(out/'controlled_regional_effects.png',dpi=160);plt.close(fig)

    out=ROOT/'results/vintage_sensitivity_v1'
    m=pd.read_csv(out/'metrics_macro.csv')
    p=m.pivot(index=['model','mode'],columns='scenario',values='scaled').reset_index()
    p['increase_pct']=100*(p.git_snapshot_at_India_midnight/p.ideal_retrospective-1)
    text='''# Recorded-source availability sensitivity v1

Completed retrospective two-date panel:48 fresh inference tasks and672 forecast-day predictions,
three states, issue dates1September/1October2026, history/calendar modes, both pinned TSFMs.
The protocol was recorded before these new outcomes. No future prospective observations were retrieved.

At midnight India time, the last recorded Git snapshot before the issue cutoff ends30August or28September:
two/three calendar days behind the issue date. The ideal retrospective scenario instead supplies observations
through issue−1. The available-context scenario never fabricates those missing trailing labels; it starts
forecasting after the last recorded label and extends the horizon so BOTH scenarios score the same14
issue-relative target dates. Forecast-origin and issue-relative leads are saved separately. All inputs and
fitting choices remain past-only; no calibration or feature selection is performed on these cases.

## Mean scaled error over all14 target days

Equal state/issue weighting. This table is not the earlier all-year lead1/7/14 benchmark.

'''+table(p)+'''
The recorded-lag scenario has larger mean error in each tested model/mode, with increases about3.9%–11.3%.
Only two issue dates were tested; this is not a causal/general operational-performance claim.

Recorded Git timestamps are not certified first-publication times. Sparse archive evidence establishes
some older snapshots but not every origin-time release. This study models the observed Git snapshots,
not all possible reporting channels. Historical revisions and source-day conventions require separate review.
The first post-period prospective episode remains frozen and unscored; this sensitivity cannot retune it.
'''
    (out/'REPORT.md').write_text(text)

    out=ROOT/'results/stable_tree_refit_v2'
    m=pd.read_csv(out/'metrics_macro.csv');a=m[m.year.eq(2026)&m.scope.eq('all')].pivot(
        index=['mode','schedule'],columns='horizon',values='MASE').reset_index()
    text='''# Version2 tree numerical-contract study

A separate scalar implementation and pandas rolling features agree to about2.4e-11 but produce different
float64 LightGBM split decisions. Eight of twelve checked tree forecasts fail the original tight tolerance;
the largest discrepancy is4.2798GWh. Identical production arrays give exactly equal1/2-thread forecasts,
so thread count is not the demonstrated cause. Ridge examples and parameter-choice IDs reproduce, but
one validation loss and several tree forecasts do not. These failed checks are preserved in provenance_review_v1.

The mitigation was recorded before new version2 outcomes: cast the complete prescribed feature matrix,
including queries, to float32 before any tree fitting/prediction. No features/grid/score-selected changes
are made. This is a NEW numerical contract, not a silent rewrite of version1 or frozen future forecasts.
648 past-only validation fits,81 selected configurations,999 deployment fits and53622 predictions completed.
Seventeen parameter choices differ from version1 through the same pre-year validation rule; no evaluation
error chooses between the contracts.

The separate implementation in a clean environment reproduces all12 checked version2 tree forecasts and
three selected configurations exactly (max difference0). This is bounded software evidence by the same
assistant, not an independent expert or proof that all future implementations/hardware will match.

## Partial2026 macro MASE

'''+table(a)+'''
Original version1 forecasts remain historical evidence. Version2 does not establish a superior model;
the point is an explicit reproducible arithmetic interface. See clean review hashes/package versions,
including SciPy1.18.1 in the separate environment versus1.17.0 in the original numerical stack.

## Retained runner failure

All forecasts and metrics completed, but final run-metadata writing failed because a relative output path
was passed to an absolute-root hash formatter. The original traceback and execution-time runner source
are retained. The wrapper now resolves paths before delegation. `audit_stable_tree.py` independently
checked completed outputs and reconstructed run metadata without rerunning fits or modifying predictions.
Total wall time was not fabricated; deployment-fit duration sum is recorded instead. This packaging failure
is distinct from model-fit failures. No failed scientific comparison is hidden or waived.
'''
    (out/'REPORT.md').write_text(text)
    print('Gate reports and controlled-effect figure written.')


if __name__=='__main__':
    main()
