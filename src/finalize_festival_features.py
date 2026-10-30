"""Combine complete intervention cohorts and retain every prespecified arm."""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd
from festival_feature_design import ROOT, KEY, sha, dump
from report_multifestival import markdown

MODELS = ['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax', 'chronos', 'timesfm']


def score(d, out, prefix):
    d = d.copy()
    d['ae'] = abs(d.prediction-d.actual)
    d['scaled'] = d.ae/d.mase_scale
    cells = d.groupby(['family', 'model', 'arm', 'state', 'year', 'horizon']).agg(
        MAE_GWh=('ae', 'mean'), MASE=('scaled', 'mean'), n=('ae', 'size')).reset_index()
    cells.to_csv(out/f'{prefix}_metrics_state_year.csv', index=False)
    y = cells.groupby(['family', 'model', 'arm', 'year', 'horizon']).MASE.mean().reset_index()
    y.to_csv(out/f'{prefix}_metrics_year.csv', index=False)
    m = y.groupby(['family', 'model', 'arm', 'horizon']).MASE.mean().reset_index()
    m.to_csv(out/f'{prefix}_metrics_festival.csv', index=False)
    m.groupby(['model', 'arm', 'horizon']).MASE.mean().reset_index().to_csv(out/f'{prefix}_metrics_balanced.csv', index=False)
    baseline = cells[cells.arm.eq('calendar')]
    joined = cells.merge(baseline, on=['family', 'model', 'state', 'year', 'horizon'], suffixes=('', '_calendar'), validate='many_to_one')
    assert (joined.n == joined.n_calendar).all()
    joined['MASE_change'] = joined.MASE-joined.MASE_calendar
    joined['MAE_reduction_pct'] = np.where(joined.MAE_GWh_calendar > 0,
        100*(1-joined.MAE_GWh/joined.MAE_GWh_calendar), np.nan)
    joined['percentage_defined'] = joined.MAE_GWh_calendar.gt(0)
    joined.to_csv(out/f'{prefix}_paired_state_year.csv', index=False)
    yy = joined.groupby(['family', 'model', 'arm', 'year', 'horizon']).agg(
        MASE_change=('MASE_change', 'mean'), mean_MAE_reduction_pct=('MAE_reduction_pct', 'mean'),
        all_percentages_defined=('percentage_defined', 'all')).reset_index()
    yy.loc[~yy.all_percentages_defined, 'mean_MAE_reduction_pct'] = np.nan
    paired = yy.groupby(['family', 'model', 'arm', 'horizon']).agg(
        MASE_change=('MASE_change', 'mean'), mean_MAE_reduction_pct=('mean_MAE_reduction_pct', 'mean'),
        all_percentages_defined=('all_percentages_defined', 'all')).reset_index()
    paired.loc[~paired.all_percentages_defined, 'mean_MAE_reduction_pct'] = np.nan
    paired.to_csv(out/f'{prefix}_paired_festival.csv', index=False)
    contrasts = []
    pairs = [('day5', 'zero5'), ('window5', 'zero5'),
        ('day5', 'placebo_day5'), ('window5', 'placebo_window5'),
        ('offset35', 'zero35'), ('offset35', 'placebo_offset35')]
    for model, group in cells.groupby('model'):
        present = set(group.arm)
        for arm, reference in pairs:
            if not {arm, reference} <= present:
                continue
            key = ['family', 'model', 'state', 'year', 'horizon']
            c = group[group.arm.eq(arm)].merge(group[group.arm.eq(reference)], on=key, suffixes=('_arm', '_reference'), validate='one_to_one')
            assert (c.n_arm == c.n_reference).all()
            c['MASE_change'] = c.MASE_arm-c.MASE_reference
            c['arm'] = arm; c['reference'] = reference
            contrasts.append(c[key+['arm', 'reference', 'MASE_change']])
    if contrasts:
        c = pd.concat(contrasts, ignore_index=True)
        c.to_csv(out/f'{prefix}_control_contrasts_state_year.csv', index=False)
        y = c.groupby(['family', 'model', 'arm', 'reference', 'year', 'horizon']).MASE_change.mean().reset_index()
        y.groupby(['family', 'model', 'arm', 'reference', 'horizon']).MASE_change.mean().reset_index().to_csv(out/f'{prefix}_control_contrasts_festival.csv', index=False)
    return m


def main(out):
    if (out/'predictions_primary.csv').exists():
        raise FileExistsError('Preserve completed scores; version new analysis')
    p = json.loads((out/'protocol.json').read_text())
    cases = pd.read_csv(out/'primary_cases.csv')
    reference = set(map(tuple, cases[KEY].to_numpy()))
    primary, secondary = [], []
    for worker in MODELS:
        run = json.loads((out/worker/'run.json').read_text())
        assert run['protocol_sha256'] == sha(out/'protocol.json')
        assert run['predictions_sha256'] == sha(out/worker/'predictions.csv')
        d = pd.read_csv(out/worker/'predictions.csv')
        assert set(d.model) == {worker}
        assert not d.duplicated(KEY+['model', 'arm']).any()
        assert np.isfinite(d[['actual', 'prediction', 'mase_scale']]).all().all()
        selected = d.merge(cases[KEY], on=KEY, validate='many_to_one')
        selected = selected[selected.arm.isin(p['arms'])]
        assert set(selected.arm) == set(p['arms'])
        for arm, group in selected.groupby('arm'):
            assert set(map(tuple, group[KEY].to_numpy())) == reference, (worker, arm)
        primary.append(selected)
        if worker not in ['chronos', 'timesfm']:
            secondary.append(d)
    d = pd.concat(primary, ignore_index=True)
    d.to_csv(out/'predictions_primary.csv', index=False)
    m = score(d, out, 'primary')
    secondary = pd.concat(secondary, ignore_index=True)
    secondary.to_csv(out/'predictions_secondary_classical.csv', index=False)
    score(secondary, out, 'secondary_classical')
    lines = ['# Explicit festival-feature intervention', '',
        p['status'], '', '**This is an added-feature experiment. Earlier multi-festival scores were diagnostics without these event identities.**', '',
        '## Matched primary comparison', '', p['primary'], '',
        f'{len(d)} scored forecasts: {len(MODELS)}model variants x {len(p["arms"])}common arms x {len(cases)}identical cases. MASE is error, not accuracy percent; lower is better. Equal states within year, years within festival and families for overall summaries.', '',
        'All variants, including zeros and active placebos, are reported. No best-looking date, encoding, capacity setting or model is selected for future deployment from these results.', '']
    balanced = pd.read_csv(out/'primary_metrics_balanced.csv')
    for h in [1, 7, 14]:
        table = balanced[balanced.horizon.eq(h)].pivot(index='model', columns='arm', values='MASE').reindex(index=MODELS, columns=p['arms']).round(5).reset_index()
        lines += [f'### Individual lead {h}', '', markdown(table), '']
    lines += ['## Per-festival and individual-year results', '',
        'See primary_metrics_festival.csv, primary_metrics_state_year.csv and primary_paired_festival.csv. Paired percent reductions are means of within-state/year effects, not ratios of macro MASE. Zero denominators remain explicitly undefined; no epsilon or silent deletion. MASE changes remain available. Negative effects and all control outcomes are retained.', '',
        '## Wider classical cohort', '', p['secondary'], '',
        'secondary_classical_* files retain every classical arm, including35offset/zero/placebo sensitivities where prespecified. Foundation-model anchor metrics must not be compared with these wider-window metrics.', '',
        '## Bounds', '',
        'Two historical years and related states/dates provide limited independent evidence. Calendar definitions are annual-as-issued, not full amendment certification or proof of statewide closure. Diwali is the legacy main/subsidiary subset. Dussehra2025/Gandhi and spring2025/Eid co-occur. New target values never enter inputs, but retrospective publication availability and pretraining/proxy overlap remain unresolved.', '',
        'One fixed placebo seed and these representations do not establish causality or a universal event-information mechanism. Rare day indicators may be below a tree leaf constraint; capacity2 is a separate fixed sensitivity, not an outcome-selected best regime. Native quantile failures are reported separately and retained without sorting/clipping. Point-metric audits are not calibration or independent human approval.', '',
        'Source permission, amendments, human review and prospective outcomes remain pending. Original source/forecast results and future Git blobs remain unchanged. No journal readiness, acceptance or new architectural method is claimed.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    dump(out/'run.json', dict(status='completed', models=MODELS, common_arms=p['arms'], cases_per_arm=len(cases),
        primary_rows=len(d), secondary_classical_rows=len(secondary),
        protocol_sha256=sha(out/'protocol.json'), primary_sha256=sha(out/'predictions_primary.csv'),
        secondary_sha256=sha(out/'predictions_secondary_classical.csv')))
    print('COMPLETED', out.name, len(d), 'primary rows;', len(secondary), 'secondary classical rows')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, default=ROOT/'results/festival_features_v1')
    main(p.parse_args().out.resolve())
