"""Independent persisted-case/label/lead/metric audit for vintage sensitivity."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data


def main():
    out=ROOT/'results/vintage_sensitivity_v1'
    d=pd.read_csv(out/'predictions.csv',parse_dates=['issue','date','first_unseen'])
    assert len(d)==672 and not d.duplicated(['state','issue','lead','model','mode','scenario']).any()
    assert np.isfinite(d.prediction).all()
    assert ((d.date-d.issue).dt.days==d.lead-1).all()
    assert ((d.date-d.first_unseen).dt.days==d.forecast_lead-1).all()
    reference=None
    for _,g in d.groupby(['model','mode','scenario']):
        cases=set(map(tuple,g[['state','issue','lead']].to_numpy()))
        if reference is None:reference=cases
        assert cases==reference
    source=load_data('latest')
    for state,g in d.groupby('state'):
        np.testing.assert_allclose(g.actual,source[state].reindex(g.date))
        a=source[state].loc['2024-01-02':'2025-12-31']
        np.testing.assert_allclose(g.mase_scale,(a-a.shift(7)).abs().mean())
    snapshots=json.loads((ROOT/'results/provenance_review_v1/git_vintage_audit.json').read_text())['snapshots']
    records={pd.Timestamp(v['issue_date_India']):v for v in snapshots if v.get('commit') and v.get('issue_date_India')}
    tasks=json.loads((out/'tasks.json').read_text())
    for task in tasks:
        issue=pd.Timestamp(task['issue_date'])
        assert pd.Timestamp(task['last_context_date'])<issue
        assert pd.Timestamp(task['first_unseen'])==pd.Timestamp(task['last_context_date'])+pd.Timedelta(days=1)
        assert task['horizon_offset']==(issue-pd.Timestamp(task['first_unseen'])).days
        if task['scenario']!='ideal_retrospective':
            v=records[issue]
            assert pd.Timestamp(v['recorded_commit_utc'])<=pd.Timestamp(v['cutoff_utc'])
            raw=Path('/workspace/source-vintage-cache')/(v['commit']+'.csv')
            assert hashlib.sha256(raw.read_bytes()).hexdigest()==v['sha256']
            assert task['last_context_date']==v['last_source_date']
    d['scaled']=abs(d.actual-d.prediction)/d.mase_scale
    computed=d.groupby(['model','state','issue','mode','scenario']).scaled.mean().groupby(['model','mode','scenario']).mean().sort_index()
    saved=pd.read_csv(out/'metrics_macro.csv').set_index(['model','mode','scenario']).scaled.sort_index()
    np.testing.assert_allclose(computed,saved,rtol=1e-12)
    (out/'audit.json').write_text(json.dumps(dict(status='passed',rows=len(d),cases_per_model_mode_scenario=len(reference),
        checks=['source labels/scales','unique finite predictions','identical issue-relative targets','first-unseen lead mapping',
                'context strictly before issue','recorded commits before midnight cutoff','snapshot byte hashes','macro metrics recomputed'],
        caveat='Recorded snapshot availability only, not all publishing channels or complete first-publication certification'),indent=2)+'\n')
    print('Vintage sensitivity audit passed:',len(d),'rows')


if __name__=='__main__':
    main()
