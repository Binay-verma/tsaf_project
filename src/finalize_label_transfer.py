"""Report complete supervised-family-label transfer, with all row controls."""
from datetime import datetime, timezone
import json
import numpy as np
import pandas as pd
from festival_label_transfer_v2 import OUT
from festival_label_transfer import WORKERS, FEATURES, POLICIES
from festival_feature_design import KEY, sha, dump
from report_multifestival import markdown


def main():
    if (OUT/'run.json').exists():
        raise FileExistsError('Preserve completed analysis')
    protocol = json.loads((OUT/'protocol.json').read_text())
    cases = pd.read_csv(OUT/'cases.csv')
    expected = set(map(tuple, cases[['cohort']+KEY].to_numpy()))
    arms = [f'{feature}__{policy}' for feature in FEATURES for policy in POLICIES]
    chunks = []
    for model in WORKERS:
        run = json.loads((OUT/model/'run.json').read_text())
        assert run['predictions_sha256'] == sha(OUT/model/'predictions.csv')
        assert run['protocol_sha256'] == sha(OUT/'protocol.json')
        d = pd.read_csv(OUT/model/'predictions.csv')
        assert set(d.model) == {model} and set(d.arm) == set(arms)
        assert len(d) == 1296 and np.isfinite(d[['actual', 'prediction', 'mase_scale']]).all().all()
        for _, g in d.groupby('arm'):
            assert set(map(tuple, g[['cohort']+KEY].to_numpy())) == expected
        chunks.append(d)
    d = pd.concat(chunks, ignore_index=True)
    assert len(d) == 3888 and not d.duplicated(['cohort', 'model', 'arm']+KEY).any()
    d.to_csv(OUT/'predictions.csv', index=False)
    d['MAE_GWh'] = abs(d.prediction-d.actual); d['MASE'] = d.MAE_GWh/d.mase_scale
    cells = d.groupby(['cohort', 'family', 'model', 'arm', 'state', 'year', 'horizon']).agg(
        MAE_GWh=('MAE_GWh', 'mean'), MASE=('MASE', 'mean'), n=('MASE', 'size')).reset_index()
    assert cells.n.eq(1).all()
    cells.to_csv(OUT/'metrics_state_year.csv', index=False)
    years = cells.groupby(['cohort', 'family', 'model', 'arm', 'year', 'horizon']).MASE.mean().reset_index()
    years.to_csv(OUT/'metrics_year.csv', index=False)
    families = years.groupby(['cohort', 'family', 'model', 'arm', 'horizon']).MASE.mean().reset_index()
    families.to_csv(OUT/'metrics_festival.csv', index=False)
    balanced = families.groupby(['cohort', 'model', 'arm', 'horizon']).MASE.mean().reset_index()
    balanced.to_csv(OUT/'metrics_balanced.csv', index=False)
    pairs = []
    for feature in FEATURES:
        for reference in ['exclude_control', 'all_rows']:
            pairs.append((feature+'__exclude_family', feature+'__'+reference))
    for policy in POLICIES:
        pairs += [('pooled_day5__'+policy, 'calendar__'+policy), ('typed_day5__'+policy, 'pooled_day5__'+policy)]
    contrasts = []
    keys = ['cohort', 'family', 'model', 'state', 'year', 'horizon']
    for arm, reference in pairs:
        c = cells[cells.arm.eq(arm)].merge(cells[cells.arm.eq(reference)], on=keys, suffixes=('_arm', '_reference'), validate='one_to_one')
        assert len(c) == 3*144 and (c.n_arm == c.n_reference).all()
        c['arm'] = arm; c['reference'] = reference
        c['MASE_change'] = c.MASE_arm-c.MASE_reference
        c['MAE_change_GWh'] = c.MAE_GWh_arm-c.MAE_GWh_reference
        contrasts.append(c[keys+['arm', 'reference', 'MASE_change', 'MAE_change_GWh']])
    contrasts = pd.concat(contrasts, ignore_index=True)
    contrasts.to_csv(OUT/'contrasts_state_year.csv', index=False)
    cy = contrasts.groupby(['cohort', 'family', 'model', 'arm', 'reference', 'year', 'horizon']).MASE_change.mean().reset_index()
    cf = cy.groupby(['cohort', 'family', 'model', 'arm', 'reference', 'horizon']).MASE_change.mean().reset_index()
    cf.to_csv(OUT/'contrasts_festival.csv', index=False)
    cb = cf.groupby(['cohort', 'model', 'arm', 'reference', 'horizon']).MASE_change.mean().reset_index()
    cb.to_csv(OUT/'contrasts_balanced.csv', index=False)
    lines = ['# Supervised family-label exclusion and event transfer', '', protocol['status'], '',
        '3,888 forecasts: three fixed regression budgets, nine feature/row-policy arms and the same144cases across separate event and non-event cohorts. Rows, dates and leads remain matched. No best-arm selection or parameter search.', '',
        '**This is not fully unseen event exposure.** Past electricity history, annual lags and other rows containing earlier festival responses remain available. Direct own-family labels are removed from model/scaler fitting; foundation pretraining is not tested by this experiment.', '',
        'Version1stopped on an exact matching guard and is preserved. Version2preflights all141training blocks, then uses fixed same-weekday/same-year28–84day matches; longer shifts weaken seasonal comparability and are fully recorded.', '']
    for cohort in ['event', 'non_event']:
        for h in [1, 7, 14]:
            table = balanced[balanced.cohort.eq(cohort) & balanced.horizon.eq(h)].pivot(index='model', columns='arm', values='MASE').reindex(index=WORKERS, columns=arms)
            lines += ['## '+cohort+' · individual lead '+str(h), '', markdown(table.round(5).reset_index()), '']
    lines += ['## Read the controls', '',
        'Compare pooled_day5 with calendar under exclude_family to assess pooled-feature usefulness without direct own-family fitting labels. Compare exclude_family with exclude_control for the same feature to separate removal of own-family labels from the same number of ordinary labels. Compare with all_rows to show the full-data reference. All parameters are fixed; these budgets differ from earlier validation-selected models and are not interchangeable ranking entries.', '',
        'Negative MASE_change favours the first arm. Individual state/year/lead cells and every family remain available. This is exploratory historical evidence, with two years and correlated states/dates. No causal mechanism, clean-test transfer, universal benefit, calibrated uncertainty or new-method novelty is established. Source rights, amendments, independent human review and later/source-independent confirmation remain open. Original results and prospective forecasts remain unchanged.']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    dump(OUT/'run.json', dict(status='completed', completed_utc=datetime.now(timezone.utc).isoformat(), rows=len(d),
        cases_per_model_arm=144, workers=WORKERS, arms=arms, predictions_sha256=sha(OUT/'predictions.csv'),
        protocol_sha256=sha(OUT/'protocol.json'), analysis_source_sha256=sha(__file__)))
    print('COMPLETE supervised-family-label transfer:', len(d), 'rows')


if __name__ == '__main__':
    main()
