"""Report interval gains/costs together; keep native points and all arms."""
from datetime import datetime,timezone
import json
import numpy as np
import pandas as pd
from native_interval_calibration import OUT,KEY
from festival_feature_design import sha,dump
from report_multifestival import markdown


def main():
    if (OUT/'metrics_macro.csv').exists():raise FileExistsError('Preservecompletedmetrics')
    d=pd.read_csv(OUT/'interval_predictions.csv');assert len(d)==4590
    assert d.groupby(KEY).prediction.nunique().eq(1).all()
    assert d.groupby(KEY).native_median.nunique().eq(1).all()
    d['coverage80']=((d.lower<=d.actual)&(d.actual<=d.upper)).astype(float)
    d['below80']=(d.actual<d.lower).astype(float);d['above80']=(d.actual>d.upper).astype(float)
    d['width80_GWh']=d.upper-d.lower;d['scaled_width80']=d.width80_GWh/d.mase_scale
    score=d.width80_GWh+10*np.maximum(d.lower-d.actual,0)+10*np.maximum(d.actual-d.upper,0)
    d['scaled_interval_score80']=score/d.mase_scale
    d['scaled_WIS80_median']=(.5*abs(d.actual-d.native_median)+.1*score)/(1.5*d.mase_scale)
    metrics=['coverage80','below80','above80','width80_GWh','scaled_width80','scaled_interval_score80','scaled_WIS80_median']
    d.to_csv(OUT/'scored_intervals.csv',index=False)
    state=d.groupby(['configuration','arm','state','horizon'])[metrics].mean().reset_index()
    n=d.groupby(['configuration','arm','state','horizon']).size();assert n.eq(15).all()
    state.to_csv(OUT/'metrics_state.csv',index=False)
    macro=state.groupby(['configuration','arm','horizon'])[[m for m in metrics if m!='width80_GWh']].mean().reset_index()
    macro.to_csv(OUT/'metrics_macro.csv',index=False)
    primary=macro[macro.horizon.isin([1,7,14])];primary.to_csv(OUT/'primary_metrics_macro.csv',index=False)
    macro[macro.configuration.str.startswith('timesfm')].to_csv(OUT/'extended_timesfm_metrics_macro.csv',index=False)
    reference=state[state.arm.eq('native')]
    joined=state.merge(reference,on=['configuration','state','horizon'],suffixes=('','_native'),validate='many_to_one')
    for name in ['coverage80','scaled_width80','scaled_interval_score80','scaled_WIS80_median']:
        joined[name+'_change']=joined[name]-joined[name+'_native']
    joined.to_csv(OUT/'contrasts_state.csv',index=False)
    joined.groupby(['configuration','arm','horizon'])[[name+'_change' for name in ['coverage80','scaled_width80','scaled_interval_score80','scaled_WIS80_median']]].mean().reset_index().to_csv(OUT/'contrasts_macro.csv',index=False)
    lines=['# Past-only calibration of native intervals','',
        'Exploratory historical study on previously inspected data. Fixed nominal80%intervals; native predictions and raw quantiles are unchanged. Both calibration rules were registered before their new comparison outcomes, with no model/method selection.','',
        'Expansion-only conformalized quantile regression is established prior work. Perstate/model/lead, use score=max(lower−actual,actual−upper) and the ceil((n+1)*0.8) order statistic; clamp expansion at zero, never shrink. FrozenSeptember uses16labels15–30September; expanding uses all labels strictly before query ORIGIN. Temporal dependence/drift mean no exchangeability-based time-series coverage guarantee.','',
        'The same15targetdates14–28October2026are scored within each state/lead. Coverage is shown with width and proper scores: wider intervals can raise coverage while worsening usefulness. No same-target calibration or forecast-origin-only purge.','',
        '## Common primary cohort: four configurations, three individual leads','',
        '1,620intervalrows:540matchedcases across configurations × three intervalarms. Negative interval-score/WIS changes favour calibration; positive width changes are costs. Coverage is a proportion, not point accuracy.','']
    for h in [1,7,14]:
        t=primary[primary.horizon.eq(h)].drop(columns=['horizon','below80','above80'])
        lines+=['### Individual lead '+str(h),'',markdown(t.round(5)),'']
    lines+=['## Additional TimesFM lead coverage','',
        'extended_timesfm_metrics_macro.csv reports all14leads on the same targetdates,3,780intervalrows including810overlapping primaryTimesFMrows. All unique historical rows total4,590. Do not double count these exports or imply Chronos was recalibrated at unarchived leads. Fresh TimesFM hindcasts reproduce all792previous point/quantile rows.','',
        '## Prospective interval annex','',
        'Rules for a separate annex were registered before new calibration outcomes. It derives native/fixed/expanding intervals from ORIGINAL TimesFM future quantiles without new future inference, copying original points/median. Its own issuedUTC/eligibility/freeze hashes are recorded separately. Original252forecasts are untouched. Samefutureepisode/source, not independentconfirmation; no future actuals, scores or automatic workflow reactivation.','',
        '## Limitations','',
        'This short daily panel does not establish calibration across all festivals, seasons or sources. Native event-feature undercoverage in2024–2025is not repaired by this different-cohort daily experiment. No hyperparameter/window/nominal-level search or attractive-coverage winner selection. Source publication lag/revisions, rights, full amendments, independent human review and adequate fresh confirmation remain open. Native fine-grid crossings elsewhere remain visible.']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    dump(OUT/'scoring_run.json',dict(status='completed',completed_utc=datetime.now(timezone.utc).isoformat(),
        primary_rows=1620,extended_timesfm_rows=3780,overlap_rows=810,unique_rows=len(d),
        interval_predictions_sha256=sha(OUT/'interval_predictions.csv'),scored_intervals_sha256=sha(OUT/'scored_intervals.csv'),
        point_and_native_median_unchanged_across_arms=True))
    print('Scored4590historicalintervals;native/fixed/expanding,allcasesretained')


if __name__=='__main__':main()
