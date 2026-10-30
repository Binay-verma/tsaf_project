"""Separate uncertainty supplement; preserve every earlier manuscript/deck."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from build_journal_draft import format_docx
from forecasting import ROOT
from report_multifestival import markdown

RESULT=ROOT/'results/native_calibration_v1';ANNEX=ROOT/'results/prospective_interval_20261030_v1'
OUT=ROOT/'manuscript/calibration_update_v1'
MODELS=['chronos_history','chronos_calendar','timesfm_history','timesfm_calendar']
ARMS=['native','frozen_september','expanding_past']
NAMES={'chronos_history':'Chronos history','chronos_calendar':'Chronos calendar','timesfm_history':'TimesFM history','timesfm_calendar':'TimesFM calendar'}
ARM_NAMES={'native':'Native','frozen_september':'Frozen Sept','expanding_past':'Expanding past'}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if OUT.exists():raise FileExistsError('Versionnewmanuscript;preservepriorreviewdrafts')
    for name in ['independent_audit.json','input_audit.json']:assert json.loads((RESULT/name).read_text())['status']=='pass'
    OUT.mkdir(parents=True);metrics=pd.read_csv(RESULT/'primary_metrics_macro.csv');contrasts=pd.read_csv(RESULT/'contrasts_macro.csv')
    row_order=[(model,arm) for model in MODELS for arm in ARMS[1:]]
    fig,axes=plt.subplots(1,2,figsize=(12.5,5.6),sharey=True)
    for ax,field,title in zip(axes,['coverage80_change','scaled_WIS80_median_change'],['Coverage change (percentage points)','WIS change (negative is lower error)']):
        a=contrasts[contrasts.horizon.isin([1,7,14])&contrasts.arm.ne('native')].pivot(index=['configuration','arm'],columns='horizon',values=field).reindex(row_order)[[1,7,14]]
        if field.startswith('coverage'):a=a*100
        values=a.to_numpy();limit=max(abs(values).max(),.001)
        im=ax.imshow(values,aspect='auto',cmap='RdBu_r',vmin=-limit,vmax=limit)
        ax.set_xticks(range(3),['Lead1','Lead7','Lead14']);ax.set_yticks(range(8),[NAMES[m]+' · '+ARM_NAMES[a] for m,a in row_order],fontsize=9)
        ax.set_title(title,fontsize=12)
        for i in range(8):
            for j in range(3):ax.text(j,i,f'{values[i,j]:+.1f}' if field.startswith('coverage') else f'{values[i,j]:+.3f}',ha='center',va='center',fontsize=10,color='white' if abs(values[i,j])>.65*limit else 'black')
        fig.colorbar(im,ax=ax,shrink=.8)
    fig.suptitle('Past-only interval expansion: coverage gains and score costs',fontsize=14)
    fig.tight_layout(rect=[0,0,1,.94])
    for ext in ['png','pdf','svg']:fig.savefig(OUT/f'coverage_and_WIS_changes.{ext}',dpi=220)
    plt.close(fig)
    svg=OUT/'coverage_and_WIS_changes.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    freeze=json.loads((ANNEX/'freeze.json').read_text());audit=json.loads((RESULT/'independent_audit.json').read_text())
    lines=['# Past-only native interval calibration and prospective annex','',
        '**Binay Verma · Research update · 30 October 2026 · Author/professor review draft**','',
        'This supplements the integrated journal draft without replacing its results. Q1 remains a target; source terms, calendar amendments, independent human review and adequate untouched/source-independent evidence remain open.','',
        '## Question and fixed design','',
        'Can a standard past-only adjustment improve native uncertainty without selecting intervals to match evaluated coverage? Point forecasts, medians and raw quantiles are unchanged. Native, frozen-September and expanding-past arms were fixed before the new comparison outcomes; both calibration methods were retained in the future annex before these historical coverage scores were inspected.','',
        'Expansion-only conformalized quantile regression uses s=max(lower−actual, actual−upper), the ceil((n+1)×0.8) order statistic, and nonnegative expansion max(0,s_order). The interval becomes [lower−expansion,upper+expansion]. There is no interpolation, shrinking, nominal-level/window search, cross-state pooling or selection of a best method from new errors. This is established prior work [1], not a new algorithm. Temporal dependence, changing contexts and distribution drift prevent claiming an exchangeability-based time-series coverage guarantee.','',
        'Each configuration/state/individual lead uses only calibration LABEL dates strictly before the query ORIGIN. Frozen calibration uses 16 labels from 15–30 September 2026. Expanding calibration uses all available labels from 15 September up to origin−1; counts vary from 16 to 43 in evaluation. Origin rather than target-date purging prevents long-lead label leakage.','',
        'The common cohort has 15 target dates, 14–28 October, in each state at leads 1/7/14 for all four foundation configurations. This gives 540 cases across configurations, repeated across three interval arms (1,620 rows). Fresh TimesFM inference on the original 171 contexts per mode preserves all 14 leads and reproduces all 792 earlier point/quantile rows. Its extended export has 3,780 interval rows including 810 overlapping common rows; unique historical rows total 4,590. Chronos is reused at its three archived leads only.','',
        'All historical data were already inspected; this is exploratory. The start date follows the September month boundary and maximum 14-day lead so the earliest origin has 16 calibration labels, rather than being chosen for good coverage. The new cohort is a subset of the previous 44-target-date daily panel; do not compare their aggregate scores as identical cohorts.','',
        '## Results: coverage with width and proper scores','',
        'Coverage is a proportion; width and scores are scaled by the same unchanged pre-2026 state reference. Lower interval score/WIS is better. WIS here combines one 80% interval with the unchanged native median; it is not a full-grid distributional score. All states, arms and leads are retained.','']
    for h in [1,7,14]:
        table=metrics[metrics.horizon.eq(h)].set_index(['configuration','arm']).reindex([(m,a) for m in MODELS for a in ARMS]).reset_index()
        table=table[['configuration','arm','coverage80','scaled_width80','scaled_interval_score80','scaled_WIS80_median']]
        table.configuration=table.configuration.map(NAMES);table.arm=table.arm.map(ARM_NAMES)
        table.columns=['Configuration','Method','Coverage80','Scaled width','Interval score','WIS80']
        table.to_csv(OUT/f'lead_{h}_table.csv',index=False)
        lines+=['### Individual lead '+str(h),'',markdown(table.round(4)),'']
    lines+=['![Calibration effects](coverage_and_WIS_changes.png)','',
        '*Figure 1. All common-cohort calibration contrasts relative to native intervals. Coverage and WIS use separate colour scales and units. Higher coverage is not automatically better uncertainty: widening can raise coverage and worsen WIS. See the tables for width costs.*','',
        'Some next-day coverage increases accompany small score improvements, but this is not universal. At lead 7, expansion generally raises coverage above an already near-nominal native level and worsens WIS. Lead 14 can remain below 80% despite expansion. A calibration transformation does not guarantee calibrated future intervals or improve unchanged point forecasts. The earlier festival-feature undercoverage is a different cohort and has not been solved by this daily experiment.','',
        '## Prospective interval annex: issued, not yet scored','',
        f'A separate annex was issued at {freeze["issued_utc"]} (20:42:14 India time on 30 October), from ORIGINAL TimesFM future quantiles and points. No new future model inference or future actual retrieval occurred. Both fixed and expanding methods were issued before inspecting new historical calibration coverage results. The public first checkpoint is 29bdd984770904a032cebe9efcd2a12a8d5ffc17, remote-verified before eligible target dates. This is an auditable Git checkpoint, not external preregistration.','',
        'There are 252 interval records and 216 eligible records: 72 original TimesFM future cases × three interval arms. Eligible targets are 31 October–11 November; earlier 29/30 October targets are excluded. This is the SAME forecast episode/source as the original freeze, not independent replication or 216 independent cases. The original six-configuration 252-row forecast/protocol/freeze remains byte-identical to its original Git blobs. The annex has its own later issuance and is never backdated.','',
        '**Future results remain pending.** The manual scorer cannot read labels or score before the complete target period ends. Afterwards it requires the original collector’s exact completed actual snapshot/vintage, source/metadata hashes, GWh units, complete positive labels, actual retrieval timing and first-annex-Git-commit equality. It never chooses a later vintage after viewing errors. The automatic workflow remains paused; no background scoring is promised.','',
        '## Reproduction and remaining limits','',
        f'Internal independent date/NumPy input reconstruction passes for all 342 new task inputs; the stdlib audit reconstructs calibration dates/ranks, original scales, intervals, scores, macro weights and the annex. All {audit["protected_prior_hashes_unchanged"]} protected prior scientific/code/presentation/manuscript files are unchanged. Fifty-three tests pass in working and separate clean environments, including future-label perturbation and prospective date/completeness guards. These are internal software checks, not independent human review.','',
        'One short retrospective period, related states, overlapping horizons, limited calibration labels, source revisions/report-day ambiguity and unknown source reuse terms limit generalisation. Native quantile crossings in older studies remain preserved; current TimesFM all-lead outputs have no crossing, which does not prove calibration. Prior numerical matrix discrepancies remain retained. No new-method, universal improvement, completed future accuracy, independent approval or Q1 submission readiness is claimed.','',
        '## Reference','',
        '[1] Yaniv Romano, Evan Patterson and Emmanuel J. Candès (2019), *Conformalized Quantile Regression*, arXiv:1905.03222v1. Primary metadata verified during this phase: https://arxiv.org/abs/1905.03222 . Applying this established method is not a novelty claim.','',
        'Full protocols/rows/audits: results/native_calibration_v1 and results/prospective_interval_20261030_v1. Earlier integrated draft: manuscript/journal_draft_v1. The new annex remains pending rather than being presented as future evidence already obtained.']
    md=OUT/'CALIBRATION_UPDATE.md';md.write_text('\n'.join(lines)+'\n')
    subprocess.run(['pandoc',str(md),'--from=gfm','--to=docx','--standalone','--resource-path='+str(OUT),
        '--reference-doc='+str(ROOT/'manuscript/journal_draft_v1/reference.docx'),'-o',str(OUT/'Calibration_Update_Binay_Verma.docx')],check=True)
    format_docx(OUT/'Calibration_Update_Binay_Verma.docx')
    (OUT/'build.json').write_text(json.dumps(dict(status='editable_supplement_created_PDF_QA_pending',created_utc=datetime.now(timezone.utc).isoformat(),
        source_hashes={str(path.relative_to(ROOT)):sha(path) for path in [RESULT/'primary_metrics_macro.csv',RESULT/'contrasts_macro.csv',ANNEX/'freeze.json']},
        manuscript_sha256=sha(md),builder_sha256=sha(__file__)),indent=2)+'\n')
    print('Created separate calibration review supplement; previouspaper unchanged')


if __name__=='__main__':main()
