"""Require every registered cell, then report all breadth contrasts/intervals."""
from datetime import datetime, timezone
import json
import numpy as np
import pandas as pd
from breadth_study import OUT, ROOT, MODELS, ARMS, KEY, sha, dump
from finalize_festival_features import score
from report_multifestival import markdown


def aggregate(d, metrics):
    cell = d.groupby(['family','model','arm','state','year','horizon'])[metrics].mean().reset_index()
    year = cell.groupby(['family','model','arm','year','horizon'])[metrics].mean().reset_index()
    family = year.groupby(['family','model','arm','horizon'])[metrics].mean().reset_index()
    macro = family.groupby(['model','arm','horizon'])[metrics].mean().reset_index()
    return cell, family, macro


def main():
    if (OUT/'run.json').exists():
        raise FileExistsError('Preserve completed analysis')
    reg = json.loads((OUT/'registration.json').read_text())
    summaries = {}
    for cohort, protocol_hash in reg['cohorts'].items():
        out = OUT/cohort
        assert sha(out/'protocol.json') == protocol_hash
        p = json.loads((out/'protocol.json').read_text())
        cases = pd.read_csv(out/'primary_cases.csv')
        expected = set(map(tuple, cases[KEY].to_numpy()))
        chunks = []
        for model in MODELS:
            r = json.loads((out/model/'run.json').read_text())
            assert r['protocol_sha256'] == protocol_hash
            assert r['predictions_sha256'] == sha(out/model/'predictions.csv')
            d = pd.read_csv(out/model/'predictions.csv')
            assert len(d) == len(cases)*len(ARMS) and set(d.arm) == set(ARMS)
            assert set(d.model) == {model} and not d.duplicated(KEY+['arm']).any()
            for arm, group in d.groupby('arm'):
                assert set(map(tuple, group[KEY].to_numpy())) == expected, (model,arm)
            assert np.isfinite(d[['actual','prediction','mase_scale']]).all().all()
            assert d.actual.gt(0).all() and d.mase_scale.gt(0).all()
            chunks.append(d)
        d = pd.concat(chunks, ignore_index=True)
        assert len(d) == len(cases)*48
        d.to_csv(out/'predictions_primary.csv', index=False)
        score(d, out, 'primary')
        cells = pd.read_csv(out/'primary_metrics_state_year.csv')
        keys = ['family','model','state','year','horizon']
        contrasts = []
        for arm, ref in reg['primary_contrasts']+reg['control_contrasts']:
            a = cells[cells.arm.eq(arm)].merge(cells[cells.arm.eq(ref)], on=keys,
                suffixes=('_arm','_reference'), validate='one_to_one')
            assert a.n_arm.eq(a.n_reference).all()
            a['arm'], a['reference'] = arm, ref
            a['MASE_change'] = a.MASE_arm-a.MASE_reference
            a['MAE_change_GWh'] = a.MAE_GWh_arm-a.MAE_GWh_reference
            contrasts.append(a[keys+['arm','reference','MASE_change','MAE_change_GWh']])
        paired = pd.concat(contrasts, ignore_index=True)
        paired.to_csv(out/'contrasts_state_year.csv', index=False)
        yr = paired.groupby(['family','model','arm','reference','year','horizon'])[['MASE_change','MAE_change_GWh']].mean().reset_index()
        fam = yr.groupby(['family','model','arm','reference','horizon'])[['MASE_change','MAE_change_GWh']].mean().reset_index()
        bal = fam.groupby(['model','arm','reference','horizon'])[['MASE_change','MAE_change_GWh']].mean().reset_index()
        yr.to_csv(out/'contrasts_year.csv', index=False)
        fam.to_csv(out/'contrasts_festival.csv', index=False)
        bal.to_csv(out/'contrasts_balanced.csv', index=False)
        # Leave-family-out is a descriptive composition sensitivity, not a new test.
        omissions = []
        if cohort == 'event_window':
            for family in sorted(fam.family.unique()):
                a = fam[~fam.family.eq(family)].groupby(['model','arm','reference','horizon']).MASE_change.mean().reset_index()
                a['omitted_family'] = family; omissions.append(a)
            pd.concat(omissions).to_csv(out/'leave_family_out.csv',index=False)
        qd = d[d.model.isin(['chronos','timesfm'])].copy()
        q = qd[[f'q_{100*k:03d}' for k in range(1,10)]].to_numpy()
        assert np.isfinite(q).all()
        y, scale = qd.actual.to_numpy(), qd.mase_scale.to_numpy()
        low, med, high = q[:,0],q[:,4],q[:,8]
        invalid = low>high
        qd['invalid80'] = invalid
        qd['common_crossings'] = (np.diff(q,axis=1)<0).sum(axis=1)
        residual = y[:,None]-q
        tau = np.arange(1,10)/10
        qd['scaled_mean_pinball'] = np.maximum(tau*residual,(tau-1)*residual).mean(axis=1)/scale
        interval_score = high-low+10*np.maximum(low-y,0)+10*np.maximum(y-high,0)
        qd['coverage80'] = np.where(invalid,np.nan,((low<=y)&(y<=high)).astype(float))
        qd['scaled_width80'] = np.where(invalid,np.nan,high-low)/scale
        qd['scaled_WIS80_median'] = np.where(invalid,np.nan,(.5*abs(y-med)+.1*interval_score)/1.5)/scale
        metrics=['scaled_mean_pinball','coverage80','scaled_width80','scaled_WIS80_median']
        qd.to_csv(out/'native_uncertainty_cases.csv',index=False)
        qc,qf,qm = aggregate(qd, metrics)
        # An invalid endpoint makes its interval summaries undefined; no dropped cases.
        bad = qd.groupby(['model','arm','horizon']).invalid80.any()
        for (model,arm,h),v in bad.items():
            if v:
                for table in [qc,qf,qm]:
                    table.loc[table.model.eq(model)&table.arm.eq(arm)&table.horizon.eq(h),metrics[1:]]=np.nan
        qc.to_csv(out/'native_uncertainty_state_year.csv',index=False)
        qf.to_csv(out/'native_uncertainty_festival.csv',index=False)
        qm.to_csv(out/'native_uncertainty_balanced.csv',index=False)
        m = pd.read_csv(out/'primary_metrics_balanced.csv')
        lines = ['# Matched feature breadth — '+cohort,'',p['status'],'',
            f'{len(d):,} forecasts; {len(cases)} identical cases per model/arm; all six variants/eight arms. Individual lead errors, not week-average forecasts. Lower MASE is better.','',
            'Event summaries weight states within year, years within family, then families equally. Ordinary summaries weight states and years equally; monthly dates form a bounded calendar-selected sample. No row-independent significance or generalisation from two years.','']
        for h in [1,7,14]:
            table = m[m.horizon.eq(h)].pivot(index='model',columns='arm',values='MASE').reindex(index=MODELS,columns=ARMS)
            lines += [f'## Lead {h}','',markdown(table.round(5).reset_index()),'']
        lines += ['## Native uncertainty','',markdown(qm.round(5)),'',
            'Native intervals are uncalibrated and unchanged. Coverage accompanies width/pinball and one-interval WIS; WIS=(0.5*median absolute error+0.1*80%interval score)/1.5. No marginal sorting or clipping. Invalid intervals propagate undefined scores.','',
            'Paired contrasts, both years, each family and leave-family-out sensitivity are retained. Historical/proxy overlap, publication lag/revisions, complete amendments, source rights and human review remain unresolved. Ordinary-day and event scores describe different cohorts. No causal mechanism, universal winner, untouched test or new independent events are inferred.']
        (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
        summaries[cohort]=dict(rows=len(d),cases_per_arm=len(cases),invalid80=int(invalid.sum()),
            common_crossing_pairs=int(qd.common_crossings.sum()),predictions_sha256=sha(out/'predictions_primary.csv'))
    assert sum(r['rows'] for r in summaries.values()) == reg['planned_rows']
    dump(OUT/'run.json',dict(status='completed',completed_utc=datetime.now(timezone.utc).isoformat(),
        registration_sha256=sha(OUT/'registration.json'),cohorts=summaries))
    print(json.dumps(summaries,indent=2))


if __name__ == '__main__':
    main()
