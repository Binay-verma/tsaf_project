"""Complete-cohort pooled comparisons; no best-arm selection."""
from datetime import datetime, timezone
import json
import numpy as np
import pandas as pd
from pooled_festival_experiment import OUT, COHORTS, ARMS
from festival_feature_design import KEY, sha, dump
from finalize_festival_features import score, MODELS
from report_multifestival import markdown

REUSED = ['calendar', 'day5', 'window5']
PAIRS = [('day5', 'pooled_day5'), ('window5', 'pooled_window5'),
    ('pooled_day5', 'pooled_day1'), ('pooled_window5', 'pooled_window1'),
    ('pooled_day1', 'zero1'), ('pooled_window1', 'zero1'), ('zero1', 'calendar')]


def main():
    registration = json.loads((OUT/'registration.json').read_text())
    for name, parent in COHORTS.items():
        out = OUT/name
        if (out/'predictions_primary.csv').exists():
            raise FileExistsError('Preserve completed analysis')
        p = json.loads((out/'protocol.json').read_text())
        assert sha(out/'protocol.json') == registration['protocols'][name]
        cases = pd.read_csv(out/'primary_cases.csv')
        expected = set(map(tuple, cases[KEY].to_numpy()))
        assert sha(parent/'predictions_primary.csv') == p['parent_combined_sha256']
        prior = pd.read_csv(parent/'predictions_primary.csv')
        prior = prior[prior.arm.isin(REUSED)]
        assert len(prior) == 6*3*72
        chunks = [prior]
        for model in MODELS:
            run = json.loads((out/model/'run.json').read_text())
            assert run['predictions_sha256'] == sha(out/model/'predictions.csv')
            assert run['protocol_sha256'] == sha(out/'protocol.json')
            assert run['rows'] == 5*72 and run['arms'] == ARMS
            d = pd.read_csv(out/model/'predictions.csv')
            assert set(d.model) == {model} and set(d.arm) == set(ARMS)
            chunks.append(d)
        d = pd.concat(chunks, ignore_index=True)
        assert len(d) == 3456 and not d.duplicated(KEY+['model', 'arm']).any()
        assert np.isfinite(d[['prediction', 'actual', 'mase_scale']]).all().all()
        for _, group in d.groupby(['model', 'arm']):
            assert set(map(tuple, group[KEY].to_numpy())) == expected
        d.to_csv(out/'predictions_primary.csv', index=False)
        score(d, out, 'primary')
        cells = pd.read_csv(out/'primary_metrics_state_year.csv')
        keys = ['family', 'model', 'state', 'year', 'horizon']
        contrasts = []
        for arm, reference in PAIRS:
            c = cells[cells.arm.eq(arm)].merge(cells[cells.arm.eq(reference)], on=keys,
                suffixes=('_arm', '_reference'), validate='one_to_one')
            assert len(c) == 432 and (c.n_arm == c.n_reference).all()
            c['arm'] = arm; c['reference'] = reference
            c['MASE_change'] = c.MASE_arm-c.MASE_reference
            c['MAE_change_GWh'] = c.MAE_GWh_arm-c.MAE_GWh_reference
            c['percentage_defined'] = c.MAE_GWh_reference.gt(0)
            c['MAE_reduction_pct'] = np.where(c.percentage_defined,
                100*(1-c.MAE_GWh_arm/c.MAE_GWh_reference), np.nan)
            contrasts.append(c[keys+['arm', 'reference', 'MASE_change', 'MAE_change_GWh', 'percentage_defined', 'MAE_reduction_pct']])
        contrasts = pd.concat(contrasts, ignore_index=True)
        contrasts.to_csv(out/'contrasts_state_year.csv', index=False)
        year = contrasts.groupby(['family', 'model', 'arm', 'reference', 'year', 'horizon']).agg(
            MASE_change=('MASE_change', 'mean'), MAE_reduction_pct=('MAE_reduction_pct', 'mean'),
            percentage_defined=('percentage_defined', 'all')).reset_index()
        year.loc[~year.percentage_defined, 'MAE_reduction_pct'] = np.nan
        year.to_csv(out/'contrasts_year.csv', index=False)
        family = year.groupby(['family', 'model', 'arm', 'reference', 'horizon']).agg(
            MASE_change=('MASE_change', 'mean'), MAE_reduction_pct=('MAE_reduction_pct', 'mean'),
            percentage_defined=('percentage_defined', 'all')).reset_index()
        family.loc[~family.percentage_defined, 'MAE_reduction_pct'] = np.nan
        family.to_csv(out/'contrasts_festival.csv', index=False)
        balanced = family.groupby(['model', 'arm', 'reference', 'horizon']).agg(
            MASE_change=('MASE_change', 'mean'), MAE_reduction_pct=('MAE_reduction_pct', 'mean'),
            percentage_defined=('percentage_defined', 'all')).reset_index()
        balanced.loc[~balanced.percentage_defined, 'MAE_reduction_pct'] = np.nan
        balanced.to_csv(out/'contrasts_balanced.csv', index=False)
        lines = ['# Pooled versus separate festival features — '+name, '', p['status'], '',
            '3456forecasts:2160new pooled/zero forecasts and1296reused calendar/typed forecasts. Six variants, eight arms and72identical cases per arm. The non-event family denotes its matched event pair. Individual leads1/7/14; MASE is scaled error, lower is better.', '',
            'Separate identities versus pooled5 has equal channel count, but changes allocation and statistical sharing. Pooled1 versus pooled5 measures padding sensitivity. Neither comparison establishes causality or a universal need for identities. All model/lead/family/year outcomes are retained; no new deployment selection.', '']
        metrics = pd.read_csv(out/'primary_metrics_balanced.csv')
        for h in [1, 7, 14]:
            lines += ['## Individual lead '+str(h), '', markdown(metrics[metrics.horizon.eq(h)].pivot(index='model', columns='arm', values='MASE').reindex(index=MODELS, columns=REUSED+ARMS).round(5).reset_index()), '']
        lines += ['## Interpretation and limits', '',
            'See contrasts_balanced.csv and contrasts_festival.csv: negative MASE_change favours the first arm. Percentage reductions are averaged within state/year, not computed from the macro-MASE ratio. A zero reference remains undefined; no epsilon or dropped cases.', '',
            'All historical data were inspected previously. Two event years and three related states are limited, correlated evidence. No all-day operational, untouched, causal or architecture-superiority claim. Source rights, amendment completeness, model/source exposure and publication lag remain unresolved. No new future actuals were acquired. Frozen forecasts and paused automation are unchanged.', '',
            'Native quantiles are retained without sorting/clipping. Their crossing inventory and actual-input byte checks are in the input audit. Point metrics do not establish calibration or independent human approval.']
        (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
        dump(out/'run.json', dict(status='completed', completed_utc=datetime.now(timezone.utc).isoformat(),
            rows=len(d), new_rows=2160, reused_rows=1296, models=MODELS, arms=REUSED+ARMS,
            cases_per_model_arm=72, predictions_sha256=sha(out/'predictions_primary.csv'),
            protocol_sha256=sha(out/'protocol.json'), parent_predictions_sha256=p['parent_combined_sha256']))
        print(name, 'complete', len(d), 'rows')


if __name__ == '__main__':
    main()
