"""Audit completed float32 tree artifacts and recover metadata after path error."""
from pathlib import Path
import datetime
import hashlib
import importlib.metadata
import json
import numpy as np
import pandas as pd
from forecasting import ROOT, load_data

OUT=ROOT/'results/stable_tree_refit_v2'


def main():
    d=pd.read_csv(OUT/'predictions.csv',parse_dates=['origin','date'])
    source=load_data('latest')
    assert len(d)==53622 and set(d.model)=={'lightgbm'}
    assert not d.duplicated(['state','origin','horizon','mode','schedule']).any()
    assert np.isfinite(d.prediction).all()
    assert ((d.date-d.origin).dt.days==d.horizon-1).all()
    for state,g in d.groupby('state'):
        np.testing.assert_allclose(g.actual,source[state].reindex(g.date))
    chosen=pd.read_csv(OUT/'selected.csv');search=pd.read_csv(OUT/'selection.csv');fits=pd.read_csv(OUT/'fit_log.csv')
    keys=['state','year','horizon','mode','model']
    assert len(chosen)==81 and len(search)==648 and len(fits)==999
    np.testing.assert_allclose(chosen.set_index(keys).MAE.sort_index(),search.groupby(keys).MAE.min().sort_index())
    assert (pd.to_datetime(search.training_target_max)<pd.to_datetime(search.validation_origin_min)).all()
    assert (pd.to_datetime(search.validation_target_max).dt.year<search.year).all()
    assert (pd.to_datetime(fits.training_target_max)<pd.to_datetime(fits.refit)).all()
    matched=fits.merge(chosen[keys+['configuration']],on=keys,suffixes=('','_selected'),validate='many_to_one')
    assert matched.configuration.eq(matched.configuration_selected).all()
    d['scaled']=abs(d.actual-d.prediction)/d.mase_scale
    saved=pd.read_csv(OUT/'metrics_state_year.csv')
    computed=d.groupby(['state','year','horizon','mode','schedule']).scaled.mean().sort_index()
    recorded=saved[saved.scope.eq('all')].set_index(['state','year','horizon','mode','schedule']).MASE.sort_index()
    np.testing.assert_allclose(computed,recorded,rtol=1e-12)
    protected=json.loads((OUT/'protected_before.json').read_text())
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in protected.items())
    audit=dict(status='passed',rows=len(d),selection_fits=len(search),selected=len(chosen),deployment_fits=len(fits),
        checks=['source labels','unique finite cases','lead/date alignment','past-only selection minima and purge',
                'frozen selected configurations across refits','pre-refit fitting labels','metrics recomputed','historical data/results unchanged'])
    (OUT/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    if not (OUT/'run.json').exists():
        # Forecasts/metrics completed; only absolute-path metadata construction failed.
        metadata=dict(**audit,status_detail='completed forecasts and metrics; recovered run metadata after relative-path ValueError',
            numerical_contract='float32 full feature matrix',metadata_repaired_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            original_error='results/stable_tree_refit_v2/protocol.json not subpath of absolute ROOT',
            deployment_seconds_sum=float(fits.seconds.sum()),total_wall_seconds=None,
            packages={p:importlib.metadata.version(p) for p in ['numpy','pandas','scikit-learn','lightgbm']},
            hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [OUT/'runner_at_execution.py',ROOT/'src/robust_baselines.py',OUT/'protocol.json',
                 ROOT/'data/external/latest_state_energy_GWh.csv',Path(__file__)]})
        (OUT/'run.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':
    main()
