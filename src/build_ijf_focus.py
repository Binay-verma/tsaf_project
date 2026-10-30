"""Build a focused review draft after every breadth/comparator audit passes."""
from datetime import datetime,timezone
import json,subprocess
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from docx import Document
from breadth_study import ROOT,OUT as BREADTH,MODELS,ARMS
from festival_feature_design import sha,dump
from build_journal_draft import format_docx,NAMES
from report_multifestival import markdown

OUT=ROOT/'manuscript/ijf_focus_v2'


def table_md(frame):
    shown=frame.copy()
    for column in shown:
        if pd.api.types.is_numeric_dtype(shown[column]):
            shown[column]=shown[column].map(lambda value:'undefined' if pd.isna(value) else f'{value:.5f}')
    return markdown(shown)


def save_figure(fig,path):
    for ext in ['png','pdf','svg']:
        f=path.with_suffix('.'+ext);fig.savefig(f,dpi=180,bbox_inches='tight')
        if ext=='svg':f.write_text('\n'.join(line.rstrip() for line in f.read_text().splitlines())+'\n')
    plt.close(fig)


def main():
    if OUT.exists():raise FileExistsError('Preserve prior draft; create another version')
    required=[BREADTH/'independent_audit.json',ROOT/'results/event_comparators_v1/independent_audit.json',
        ROOT/'results/pooling_simulation_v1/independent_audit.json',ROOT/'review/clean_extended_v1/comparison.json']
    for path in required:assert json.loads(path.read_text())['status']=='pass',path
    OUT.mkdir();(OUT/'figures').mkdir()
    metrics={c:pd.read_csv(BREADTH/c/'primary_metrics_balanced.csv') for c in ['event_window','ordinary']}
    contrasts={c:pd.read_csv(BREADTH/c/'contrasts_balanced.csv') for c in metrics}
    arrays={}
    for c,d in contrasts.items():
        a=np.empty((6,6))
        for i,m in enumerate(MODELS):
            for j,(arm,h) in enumerate([(a,h) for a in ['day5','window5'] for h in [1,7,14]]):
                ref='pooled_day5' if arm=='day5' else 'pooled_window5'
                v=d[d.model.eq(m)&d.arm.eq(arm)&d.reference.eq(ref)&d.horizon.eq(h)]
                assert len(v)==1;a[i,j]=v.MASE_change.iloc[0]
        arrays[c]=a
    limit=max(float(abs(a).max()) for a in arrays.values())
    fig,axes=plt.subplots(2,1,figsize=(9,8.2),layout='constrained')
    for ax,(c,a) in zip(axes,arrays.items()):
        im=ax.imshow(a,aspect='auto',cmap='RdBu_r',vmin=-limit,vmax=limit)
        ax.set_xticks(range(6),['Day:1','Day:7','Day:14','Window:1','Window:7','Window:14'])
        ax.set_yticks(range(6),[NAMES[m] for m in MODELS],fontsize=11)
        ax.axvline(2.5,color='white',linewidth=3)
        for i in range(6):
            for j in range(6):ax.text(j,i,f'{a[i,j]:+.3f}',ha='center',va='center',fontsize=11,color='white' if abs(a[i,j])>.65*limit else 'black')
        ax.set_title('Complete festival windows' if c=='event_window' else 'Seasonal ordinary-day sample')
    fig.colorbar(im,ax=axes,label='Typed minus pooled MASE; negative favours typed')
    save_figure(fig,OUT/'figures/breadth_contrasts')
    sim=pd.read_csv(ROOT/'results/pooling_simulation_v1/paired_seed_contrasts.csv')
    s=sim[sim.arm.eq('typed_OLS')&sim.reference.eq('pooled_OLS')]
    fig,axes=plt.subplots(1,2,figsize=(10,4.2),layout='constrained',sharey=True)
    for ax,hetero in zip(axes,[0.,3.]):
        part=s[s.heterogeneity.eq(hetero)].sort_values(['frequency','date_error','noise'])
        x=np.arange(len(part));ax.errorbar(x,part.event_MAE_difference,yerr=1.96*part.MC_standard_error,fmt='o',capsize=3)
        ax.axhline(0,color='black',linewidth=1);ax.set_title('Homogeneous response' if hetero==0 else 'Heterogeneous responses')
        ax.set_xticks(x,[f'{int(r.frequency)}/{int(r.date_error)}/{int(r.noise)}' for r in part.itertuples()],rotation=45)
        ax.set_xlabel('Events per type/year / date-error bound / noise SD')
    axes[0].set_ylabel('Typed minus pooled event MAE\n(simulated units; 95% Monte Carlo intervals)')
    save_figure(fig,OUT/'figures/simulation_conditions')
    tables=[]
    for c,d in metrics.items():
        cols=['calendar','day5','pooled_day5','window5','pooled_window5']
        t=d[d.horizon.eq(1)].pivot(index='model',columns='arm',values='MASE').reindex(index=MODELS,columns=cols).rename(index=NAMES).reset_index()
        t.columns=['Model','Calendar','Typed day','Pooled day','Typed window','Pooled window']
        tables.append((c,t))
    cmp=pd.read_csv(ROOT/'results/event_comparators_v1/metrics_balanced.csv')
    t=cmp[cmp.cohort.eq('event_window')&cmp.method.isin(['response_none','response_typed','response_pooled','response_partial'])].pivot(index='method',columns='horizon',values='MASE')
    t.columns=[f'Lead {h}' for h in t.columns];t=t.reset_index()
    tables.append(('comparators',t))
    native=pd.read_csv(BREADTH/'event_window/native_uncertainty_balanced.csv')
    native=native[native.horizon.eq(1)&native.arm.isin(['calendar','day5','pooled_day5','window5','pooled_window5'])][['model','arm','coverage80','scaled_width80','scaled_WIS80_median']]
    native.columns=['Model','Arm','Coverage80','Scaled width','Scaled WIS80'];tables.append(('native',native))
    cells=[]
    for name,table in tables:
        table.to_csv(OUT/(name+'_table.csv'),index=False)
        for row in table.itertuples(index=False,name=None):
            cells += ['undefined' if pd.isna(v) else f'{v:.5f}' for v in row if isinstance(v,(float,np.floating))]
    lo,hi=float(arrays['event_window'].min()),float(arrays['event_window'].max())
    clean=json.loads((ROOT/'review/clean_extended_v1/comparison.json').read_text())
    lines=['# Sparse festival representations in foundation forecasting: matched electricity evidence and pooling controls','',
        '**Focused research draft for Binay Verma and professor review. Not submitted or submission-ready.**','',
        '**Calendar correction notice:** These tables preserve the original frozen ledger. A later document-level check found that Karnataka’s 2025 notification labels 1 October as Vijayadasami and 2 October as Gandhi Jayanthi; the ledger uses 2 October for Dussehra. Annual holiday-date membership did not verify the festival name. This known mismatch is not silently repaired in these results. See review/used_calendar_v3 and the separately versioned correction experiment before interpreting state-calendar accuracy.','',
        'Author: Binay Verma. College/department: __________. Corresponding-author email: __________. These fields are intentionally blank at the author’s request. Funding, conflicts and any real coauthor contributions remain to be completed. No professor authorship or independent review is assumed.','',
        '## Abstract','',
        f'Sparse event labels create a trade-off between response specificity and statistical sharing. We examine that trade-off in daily supplied electricity from Delhi, Karnataka and Maharashtra using five festival families, two pinned foundation models and four local model variants. A fixed exploratory extension compares eight representations on 528 complete festival-window cases and 216 calendar-selected ordinary cases per configuration, producing 35,712 forecasts. Typed and pooled flags are compared at the same five-channel event budget, with ordinary-calendar, zero and active-placebo controls. Typed-minus-pooled MASE changes across models, leads and day/window representations range from {lo:.3f} to {hi:.3f}; their interpretation is conditional on the cohort and adaptation policy. Additional past-only target-encoding and response-profile baselines contribute 5,952 matched forecasts. A prespecified 512-dataset simulation illustrates how heterogeneity, support and date errors change pooling value under a known baseline and response shape. Complete comparator/simulation reruns in a separate Python environment are byte-identical. Historical outcomes remain exploratory; correlated event years, model exposure, source-vintage/calendar uncertainty, unresolved reuse terms and absent external review limit generalisation. The contribution is a controlled empirical qualification, not a new architecture, causal effect or universal festival-enhancement claim.','',
        '**Keywords:** event representation; electricity forecasting; partial pooling; time-series foundation models; calendar provenance; temporal evaluation.','',
        '## 1. Forecasting question and related work','',
        'Separate event identities offer response specificity but have few historical examples. Pooling shares information while assuming greater response similarity. This is an established statistical trade-off. In a covariate-informed foundation model, the interface adds another complication: changing the number or allocation of channels can change forecasts even if some channels contain zeros. The practical question is when sparse event information benefits from pooling, and whether the answer survives complete event windows and ordinary-day costs.','',
        'Calendar target encodings are directly studied by Kreusel et al. [1], including Chronos-2 and TimesFM-3. Alipour et al. [2] learn impact-driven event covariates from residual responses; their primary page and linked paper have unresolved venue metadata differences. Indian moving-holiday regressors [3], covariate-uncertainty load evaluation [4], and sample/proxy leakage analysis [5] are also close antecedents. We do not claim to invent event indicators, window regressors, target encoding, pooling, residual profiles or conformal calibration.','',
        'The empirical contribution is deliberately narrower: a named-calendar evaluation with matched typed/pooled/dimension/placebo controls, explicit sparse-support/adaptation logs, complete event-window and seasonal ordinary-day comparisons, and preserved negative/numerical/provenance evidence. The known Karnataka family/date mismatch limits calendar-quality claims. Subsequent pure-encoding, NESO source/delay and document-aligned correction experiments have separate versioned results; their forecasts are not included in these original-ledger tables. Exact contrastive learned-event replication and untouched multi-event evidence remain gaps. More model names alone do not close those gaps.','',
        '## 2. Data, calendar and evaluation units','',
        'The target is daily energy met/supplied in GWh, which can reflect supply constraints; it is not latent unconstrained demand, household consumption or hourly peak load. We use a single frozen GRID-INDIA/POSOCO compilation, without splicing the earlier corrected dataset. Historical labels through 28 October 2026 have already been inspected. Every new historical method comparison is exploratory. Chronological weight identities do not clear historical or correlated-proxy overlap [5–7].','',
        'A frozen ledger contains 58 named anchors across 48 family/state/year groups in 2022–2025. Families are Holi, Dussehra, Ganesh Chaturthi, Ugadi/Gudi Padwa and Diwali, with documented state scope rather than presumed impact in every state. Karnataka 2023 Ganesh is 18 September, while Maharashtra is 19 September; Maharashtra 2023 Holi is 7 March. The legacy Diwali definition retains shared-main and subsidiary dates, including two explicit Maharashtra annual-office-date exceptions. The ledger is annual-as-issued, not fully amendment-certified; office closure is not proof of statewide response. Coincident holidays remain confounders.','',
        'The primary breadth cohort retains all 528 original window/lead cases: 176 state/target-date combinations across 24 festival/state/year groups in 2024–2025, with leads 1, 7 and 14. These are not 528 independent events. The ordinary cohort has 216 cases: one target per month/state/year, with three leads. Dates are the first eligible rotating weekday in each month, excluding ±3 days around annual-as-issued and registered holidays. Targets lie between 14 January and 18 December to keep all context/future covariates inside the audited 2022–2025 ledger. No target value or error selects dates. The bounded ordinary sample is not exhaustive all-day evaluation.','',
        'An origin is the first unseen model date; lead h targets origin+h−1. All compared arms and variants have identical cases. MASE uses each state’s pre-year 730-calendar-day mean absolute weekly difference, scoring only positive recorded labels. Event summaries average target errors within state/year/family, states within year, years within family, and then families equally. Ordinary summaries weight states and years equally. Raw daily rows, states, leads and nearby holidays are correlated. We report both years and leave-family-out composition sensitivity rather than independent-row significance or precise two-year bootstrap claims.','',
        '## 3. Models, representations and prior registration','',
        'Eight arms retain the ordinary 13-channel weekday/annual-harmonic calendar: calendar alone, five exact zeros, typed day5, pooled day5, typed window5, pooled window5, and typed day/window placebos. Pooled5 contains the logical union of state-scoped family flags in one channel plus four zeros; typed5 uses one channel per family. Windows are unions of ±3 days, not counts of subsidiary dates. Placebos use the original fixed seeded weekday-preserving shifts, avoiding registered true windows; one seed is a bounded control, not a randomisation distribution. Padding is not assumed inert and representation contrasts do not identify causal identity effects.','',
        'Pinned Chronos-2 [6] and TimesFM-3 [7] use 730 prior target days, 14 forecast steps, no task fine-tuning, seed42, two CPU threads and batch16. Every task records actual target/covariate bytes and future-target perturbation invariance; first batches are checked against solo inference. All native quantiles/crossings remain unchanged. This wider study uses fresh inference, preserving earlier anchor outputs. Model weight hashes and noncommercial TimesFM weight terms are retained in the model audits.','',
        'Local variants are rich Ridge, stable LightGBM, a separately reported leaf-minimum2 tree sensitivity, and fixed SARIMAX. Ridge/trees use 27 past-only history features plus the same calendar/event features, monthly fits and unchanged pre-year selected parameters across every arm. Trees receive float32 matrices. The leaf2 change is fixed and not selected by evaluated errors. SARIMAX uses (1,0,0)×(1,0,0,7), no trend, annual 730-day parameter fits and past-only state updates; training-convergence retries and failures remain logged. Differences in adaptation/fitting policy preclude an architecture-only attribution.','',
        'The breadth protocol was committed before new outcomes. It follows inspected anchor/pooling studies and is not an external preregistration or clean final test. The protocol, source/input hashes, full case matrix, packages, sparse support, failures, checkpoints and separate audits are available with the repository. Historical negative findings, including the original four-year Chronos seven-channel Diwali deterioration, remain unchanged.','',
        '## 4. Matched breadth results','',
        'Tables 1–2 give predeclared next-day scores for both representations; all three leads, eight arms, state-years, families and controls are retained in the machine-readable supplement. Figure 1 shows typed-minus-pooled differences for every model, representation, lead and cohort. A negative difference favours separate identities. Ordinary and event levels describe different target cohorts and are not a causal treatment/control estimate.','',
        'Table 1. Full festival-window next-day MASE. Lower is better.','',table_md(tables[0][1]),'',
        'Table 2. Calendar-selected ordinary-day next-day MASE. Lower is better.','',table_md(tables[1][1]),'',
        '![Figure 1. Typed minus pooled MASE at equal five-channel event budget. Both signs, all six variants and all three leads are retained.](figures/breadth_contrasts.png)','',
        f'The full-window typed-minus-pooled contrasts span {lo:.5f} to {hi:.5f} MASE across the registered cells. This range describes the evaluated matrix and does not select a winning method. Both-year and leave-family-out tables allow assessment of composition sensitivity; two event years and unequal state scopes still limit generality. Zero/placebo contrasts help diagnose representation sensitivity without establishing a causal mechanism.','',
        '## 5. Established-method comparators and simulation','',
        'Eight additional daily methods use exactly the same cases. Four are rolling-context weekday/holiday conditional means adapted from target-encoding ideas [1], with explicit unseen-category fallbacks. These direct point baselines omit the hourly paper’s hour variable and are not its multivariate TSFM encodings. Their weak 730-day context means do not establish that target encoding is intrinsically poor.','',
        'Four response methods share a last-four-recorded-same-weekday baseline: no response, typed OLS amplitudes, one pooled amplitude, and partial pooling with fixed penalty2 toward the pooled amplitude. Past residuals use only earlier same-weekday observations; profile training uses strictly pre-origin recorded labels. The fixed ±3-day triangular shape is declared rather than learned on test errors. This is a simple daily residual-profile adaptation, not the contrastive system of Alipour et al. [2].','',
        'Table 3. Full-window matched response-profile comparator MASE. No penalty is selected on these errors.','',table_md(tables[2][1]),'',
        'The partial-pooling response comparator improves its matching no-response baseline but remains weaker than the rich local models in Table 1 at the next-day lead. It is not a new state-of-the-art algorithm. On the selected ordinary dates, all four response methods coincide by construction because query event windows are excluded. This cannot be cited as learned spillover evidence. Direct family-label exclusion from the earlier study is a separate sensitivity: earlier family responses remain in target-history features, so it is not wholly unseen-event transfer.','',
        'A prespecified simulation crosses event frequency1/4 per family/year, heterogeneity0/3, integer date-error bound0/2days and noise SD1/3, with32seeds per setting. Five event types share a known triangular response shape and an exactly removed baseline; two years fit and one year evaluates. Noise is stationary AR(1) with coefficient0.5. No-event, pooled OLS, typed OLS, fixed partial pooling and an explicitly unavailable true-effect oracle are all retained. Figure 2 illustrates the expected trade-off: homogeneous responses favour pooling on average, while strong heterogeneity favours separate effects under this generator. This is not an explanation of neural internals or new real-world independent evidence.','',
        '![Figure 2. Conditional simulation contrasts. Intervals quantify Monte Carlo precision over independent generator seeds, not Indian-event significance.](figures/simulation_conditions.png)','',
        '## 6. Native uncertainty and reproducibility','',
        'Both foundation models are scored on unchanged common quantiles0.1–0.9. Empirical80%coverage accompanies scaled width, marginal pinball and a one-interval WIS: (0.5×median absolute error+0.1×80%interval score)/1.5. Crossings are retained; invalid endpoints make the full associated interval aggregate undefined rather than dropping cases. These are native, uncalibrated festival-feature distributions.','',
        'Table 4. Native next-day full-window intervals. Full lead1/7/14 tables and every control arm remain in the supplement.','',table_md(tables[3][1]),'',
        'The separate September–October2026 CQR exercise improves some historical coverage while widening intervals and sometimes worsening longer-lead proper scores. It uses a different cohort and does not calibrate the present festival-feature distributions. The original future point/native freeze and later interval annex remain immutable and unscored; the annex repeats existing TimesFM cases from the same episode.','',
        'Separate scalar/calendar/NumPy audits reconstruct sources, cases, scales, actual inputs, local budgets/labels/support, chronological cutoffs, probability arithmetic and aggregate metrics. Complete clean-environment reruns of all5,952daily comparator forecasts and2,560simulation cells produce byte-identical scientific output files. This uses the same machine and exact source/input copies, not an independent human team or complete new foundation-model rerun. The earlier stricter pooled scalar review retains its near-zero tree-feature byte discrepancy even though its135forecasts agree within tolerance. Passing software tests is evidence about specific checks, not proof of zero scientific error.','',
        '## 7. Limits and confirmation requirements','',
        'All historical method choices are exploratory; model/source/proxy exposure remains unresolved. Three related states and two event years do not establish broad regional or temporal generalisation. Weather, supply constraints, coincident events, annual versus amended calendars and source revisions remain possible explanations. Public source access does not itself settle redistribution rights. The author reports manually requesting clarification; no response or independent sign-off is inferred.','',
        'A separate primary-source audit acquired MTA and Elexon probes without treating them as forecast replication. The deprecated MTA view stops9January2025; an Elexon UTC week crosses a46-period local settlement day and a date boundary. A subsequent registered NESO England/Wales experiment integrates actual half-hour MW into daily GWh and compares ideal versus 21 additional days of archive delay. Its separately audited local checkpoint covers 16 ordinary September dates; the complete foundation comparison is outside this draft’s tables. These dates provide no independent holiday result or first-vintage reconstruction. Indian shared-source derivatives do not provide source independence.','',
        'A new52-week manual confirmation plan starts16November2026, but is not activated and has issued no forecasts. Its explicit two-day availability bridge maps decision leads1/7/14 to model steps3/9/16; a manifest-contract validator is not an end-to-end runner. New-year ledger, capture/runner/scorer adapters, publication/time guards, human review and actual future observations remain prerequisites. Existing prospective automation stays paused. One future event year would still provide limited annual replication.','',
        'The study therefore supports a conditional forecasting lesson about event representation and evaluation discipline. It does not yet establish a sufficiently general or distinct contribution for IJF acceptance. Before submission, reproduce the closest TSFM encodings/event methods under matched information budgets, obtain genuinely separate/untouched evidence, complete the source/calendar/independent-review gates, and verify current journal instructions and declarations.','',
        '## Data, code and author statements','',
        'Code and completed exploratory artifacts are at https://github.com/Binay-verma/tsaf_project . Model weights/caches and newly audited raw external probes are excluded. Dataset attribution and unresolved rights are explicit; no new open-data licence is granted. Original/follow-up protocols and failed attempts are retained. The official IIF states data/code sharing and an acceptance-conditional reproducibility check; any restriction needs an editor-acceptable justification. No journal submission/contact, acceptance or fee is implied.','',
        'Funding, conflicts, affiliation, corresponding-author details and any coauthor contributions await factual author confirmation. Binay Verma is author/requester, not an independent reviewer.','',
        '## References','',
        '[1] Kreusel et al. (2026). On the Encoding of Calendar Features in Covariate-Informed Time Series Foundation Models. arXiv:2610.13676v1. https://arxiv.org/abs/2610.13676','',
        '[2] Alipour et al. Impact-driven event covariates for time-series foundation models. Primary publication page; venue metadata unresolved. https://www.amazon.science/publications/impact-driven-event-covariates-for-time-series-foundation-models','',
        '[3] Sanyal, Mitra, McElroy and Roy (2017). Holiday Effects in Indian Manufacturing Series. Census RRS2017-04. https://www.census.gov/library/working-papers/2017/adrm/rrs2017-04.html','',
        '[4] Kaljevic, Arzola and Zhang (2026). Benchmarking Time Series Foundation Models for Load Forecasting Under Covariate Uncertainty. arXiv:2610.07232v1. https://arxiv.org/abs/2610.07232','',
        '[5] Meyer et al. Rethinking Evaluation in the Era of Time Series Foundation Models: (Un)known Information Leakage Challenges. arXiv:2510.13654v3. https://arxiv.org/abs/2510.13654','',
        '[6] Ansari et al. (2025). Chronos-2: From Univariate to Universal Forecasting. arXiv:2510.15821v1. https://arxiv.org/abs/2510.15821','',
        '[7] Jain and Sen (2026). TimesFM-3: A zero-shot foundation model for multivariate forecasting. Official model announcement. https://research.google/blog/timesfm-3-a-zero-shot-foundation-model-for-multivariate-forecasting/','',
        '[8] Romano, Patterson and Candès (2019). Conformalized Quantile Regression. arXiv:1905.03222v1. https://arxiv.org/abs/1905.03222','']
    md='\n'.join(lines).rstrip()+'\n'
    for old,new in {'seed42':'seed 42','two CPU threads and batch16':'two CPU threads and batch 16',
        'exact zeros, typed day5':'exact zeros, typed day5','Fixed penalty2':'Fixed penalty 2',
        'fixed penalty2':'fixed penalty 2','frequency1/4':'frequency 1/4',
        'heterogeneity0/3':'heterogeneity 0/3','bound0/2days':'bound 0/2 days',
        'noise SD1/3':'noise SD 1/3','with32seeds':'with 32 seeds',
        'quantiles0.1–0.9':'quantiles 0.1–0.9','Empirical80%coverage':'Empirical 80% coverage',
        'empirical80%coverage':'empirical 80% coverage','80%interval':'80% interval',
        'September–October2026':'September–October 2026','all5,952daily':'all 5,952 daily',
        'and2,560simulation':'and 2,560 simulation','its135forecasts':'its 135 forecasts',
        'stops9January2025':'stops 9 January 2025','a46-period':'a 46-period',
        'new52-week':'new 52-week','starts16November2026':'starts 16 November 2026',
        'lead1/7/14':'lead 1/7/14','leads1/7/14':'leads 1/7/14','steps3/9/16':'steps 3/9/16',
        'min-leaf2':'min-leaf 2','leaf-minimum2':'leaf-minimum 2','The leaf2':'The leaf2'}.items():
        md=md.replace(old,new)
    (OUT/'MANUSCRIPT.md').write_text(md)
    for value in cells:assert value in md,value
    docx=OUT/'IJF_Focused_Draft_Binay_Verma.docx'
    subprocess.run(['pandoc',str(OUT/'MANUSCRIPT.md'),'-o',str(docx),'--resource-path',str(OUT),
        '--reference-doc',str(ROOT/'manuscript/journal_draft_v1/reference.docx')],check=True)
    format_docx(docx)
    doc=Document(docx);assert len(doc.tables)==4
    dump(OUT/'qa.json',dict(status='internal_numeric_and_DOCX_pass',numeric_table_cells=len(cells),tables=4,figures=2,
        note='PDF rendering/visual review pending; not independent scientific review.'))
    inputs=[str(p.relative_to(ROOT)) for p in required]+['results/feature_breadth_v1/registration.json','results/feature_breadth_v1/scoring_registration.json',
        'results/event_comparators_v1/metrics_balanced.csv','results/pooling_simulation_v1/paired_seed_contrasts.csv','src/build_ijf_focus.py']
    for c in metrics:
        inputs += [f'results/feature_breadth_v1/{c}/{n}' for n in ['primary_metrics_balanced.csv','contrasts_balanced.csv','native_uncertainty_balanced.csv']]
    dump(OUT/'build.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),status='Review draft; not submission-ready',
        inputs={f:sha(ROOT/f) for f in inputs},outputs={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file()}))
    print('Focused MD/DOCX built;4tables/2figures checked;PDF rendering remains')


if __name__=='__main__':main()
