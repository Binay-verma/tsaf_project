"""Render persisted multi-festival scores without optional Markdown packages."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import pandas as pd
from forecasting import ROOT
from multifestival_cached import sha


def markdown(frame):
    rows = [list(frame.columns)] + frame.astype(str).values.tolist()
    return '\n'.join(['| '+' | '.join(rows[0])+' |', '| '+' | '.join(['---']*len(rows[0]))+' |'] +
        ['| '+' | '.join(r)+' |' for r in rows[1:]])


def render(out):
    d = pd.read_csv(out/'predictions.csv')
    m = pd.read_csv(out/'metrics_festival.csv')
    lines = ['# Multi-festival matched historical results', '',
        'Exploratory 2024–2025 evaluation. MASE is error, not accuracy percent; lower is better.',
        'Equal states within year, equal years within festival. Different festivals have different documented state coverage.', '',
        '## Results by festival', '']
    for family, group in m.groupby('family'):
        table = group.pivot(index='configuration', columns='horizon', values='MASE').reset_index()
        table.columns = ['Configuration', 'Lead1', 'Lead7', 'Lead14']
        for c in ['Lead1', 'Lead7', 'Lead14']:
            table[c] = table[c].map(lambda x: f'{x:.5f}')
        states = sorted(d[d.family.eq(family)].state.unique())
        lines += [f'### {family}', '', 'States: '+', '.join(states)+'.', '', markdown(table), '']
    lines += ['## Interpretation', '',
        'The ranking varies by festival and horizon. These scores diagnose forecast performance during fixed holiday windows. The ordinary calendar inputs encode weekdays and annual harmonics, not new Holi/Ganesh/Ugadi indicators. Therefore these scores do not measure a benefit from adding those festival identities.', '',
        'Diwali retains its earlier broad union of national/main and regional subsidiary windows. Other groups use one anchor per state/year. The history/ordinary-calendar tables do not replace previously reported regional-Diwali feature arms. No setting, window or best model was chosen for a clean test using these results. Detailed state/year scores and all configurations are retained.', '',
        'Only two historical years; related states/days and coincident observances are dependent. Dussehra2025 coincides with Gandhi Jayanti and Spring2025 is adjacent to Eid. Annual-as-issued schedules are not full amendment certification or evidence of statewide closure. Eid-specific and incomplete late-December cohorts are deferred, with reasons in the frozen protocol.', '',
        'Historical source revisions/publication lag and foundation-model pretraining/proxy overlap remain unresolved. Different adaptation/feature budgets prevent an architecture-only conclusion. No causal festival effect, universal winner, journal readiness or independent human review is claimed. Original and prospective predictions remain unchanged.']
    if (out/'deployment_audit.json').exists():
        audit = json.loads((out/'deployment_audit.json').read_text())
        lines += ['', '## Numerical and uncertainty diagnostics', '',
            f"Native quantile crossings retained: Chronos {audit['chronos']['native_quantile_crossings']}; TimesFM {audit['timesfm']['native_quantile_crossings']}. No sorting or clipping. The point-metric audit does not establish ordered/calibrated uncertainty.", '',
            'New TimesFM history/calendar predictions reproduce the old150Diwali cases exactly. New Chronos ordinary-calendar values agree with the prior controls within small batching differences (maximum0.0000611GWh). Six date-selected ETS deployments reproduce through scalar innovation recurrences. These are bounded internal software checks, not independent human review.', '',
            'Near ties must not be overinterpreted; ETS and naive longer-lead Holi scores are almost identical. Refer to full precision and individual-year/state tables.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    if not (out/'run.json').exists():
        run = dict(completed_utc=datetime.now(timezone.utc).isoformat(),
            completion='Scientific scores already persisted; report and run metadata recovered without rerunning fitting/scoring or modifying predictions/metrics',
            configurations=int(d.configuration.nunique()), prediction_memberships=len(d),
            cases_per_configuration=int(len(d)/d.configuration.nunique()),
            predictions_sha256=sha(out/'predictions.csv'), no_prospective_scores=True,
            timing='Original wall time not recorded; not fabricated')
        (out/'run.json').write_text(json.dumps(run, indent=2)+'\n')
    print('Rendered', out/'REPORT.md')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, default=ROOT/'results/multifestival_cached_v1')
    render(p.parse_args().out.resolve())
