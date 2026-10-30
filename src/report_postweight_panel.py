"""Recover failed textual report/metadata without rewriting audited science."""
from datetime import datetime, timezone
import json
import pandas as pd
from postweight_daily_panel import OUT
from festival_feature_design import sha, dump
from report_multifestival import markdown


def main():
    if (OUT/'run.json').exists() or (OUT/'REPORT.md').exists():
        raise FileExistsError('Preserve recovered report')
    audit = json.loads((OUT/'independent_audit.json').read_text())
    assert audit['status'] == 'pass' and audit['predictions_sha256'] == sha(OUT/'predictions.csv')
    paths = ['predictions.csv', 'metrics_state.csv', 'metrics_macro.csv', 'native_uncertainty_cases.csv',
        'native_uncertainty_state.csv', 'native_uncertainty_macro.csv', 'calendar_history_contrasts_state.csv']
    before = {f: sha(OUT/f) for f in paths}
    p = json.loads((OUT/'protocol.json').read_text())
    m = pd.read_csv(OUT/'metrics_macro.csv'); u = pd.read_csv(OUT/'native_uncertainty_macro.csv')
    native = pd.read_csv(OUT/'native_uncertainty_cases.csv')
    table = m.pivot(index='configuration', columns='horizon', values='MASE').reindex(p['configurations'])
    table.columns = ['Lead '+str(h) for h in table.columns]
    lines = ['# Daily comparison after audited weight uploads', '', p['status'], '',
        '44matched target dates15September–28October2026perstate/lead;396cases/configuration;3168forecasts across eight configurations. Earliest origin2September, after both actual weight uploads and the documented TimesFM announcement. No new source/future actuals retrieved.', '',
        'Post-weight chronology conditionally rules out direct inclusion of genuinely later observations in unchanged weights. These targets were previously inspected, so this is not untouched confirmation, proxy clearance or real-time source-vintage reconstruction.', '', markdown(table.round(5).reset_index()), '',
        '## Native uncertainty', '',
        'Common native0.1–0.9marginal quantiles; uncalibrated80%intervals, coverage with width/proper scores, one-intervalWIS plus the native median. No sorting/clipping or fitted calibration. Cases/days/states and horizons are correlated, not independent calibration trials.', '']
    for h in [1, 7, 14]:
        lines += ['### Individual lead '+str(h), '', markdown(u[u.horizon.eq(h)].drop(columns='horizon').round(5)), '']
    lines += ['## Comparison scope', '',
        'This is a bounded daily history/ordinary-calendar comparison. No added2026festival identities or full-year two-model superiority claim. All models use identical registered targets and origin-1history. Local pre2026selected rich-calendar parameters are frozen, with monthly refits and horizon-purged labels. Their raw-history warm-up can extend before the730-day label-fitting window, so memory/adaptation budgets are not architecture-identical.', '',
        'The original publication-lag/revision sensitivity, historical event results and prospective freeze remain separate and unchanged. Source terms/processing, full calendar amendments, independent human review and untouched/source-independent confirmation remain open. Workflow remains paused.', '',
        '## Report recovery', '',
        'The initial finalizer completed all scientific tables, then failed formatting integer horizon headers in Markdown. Its source/failure note are retained. The separate numerical audit passed. This recovery reads saved tables and writes only REPORT/run/recovery metadata; no forecasts, metrics or native outputs are recomputed or overwritten.']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    assert all(sha(OUT/f) == h for f, h in before.items())
    dump(OUT/'run.json', dict(status='completed', completed_utc=datetime.now(timezone.utc).isoformat(), rows=3168,
        cases_per_configuration=396, configurations=p['configurations'], native_rows=len(native),
        invalid80=int(native.invalid80.sum()), common_adjacent_crossing_pairs=int(native.common_adjacent_crossings.sum()),
        protocol_sha256=sha(OUT/'protocol.json'), predictions_sha256=sha(OUT/'predictions.csv'),
        analysis_execution_source_sha256=sha(OUT/'finalizer_execution_v1.py'), report_recovered_after_format_failure=True,
        report_recovery_source_sha256=sha(__file__)))
    dump(OUT/'report_recovery.json', dict(status='completed', scientific_files_unchanged=before,
        failure_note_sha256=sha(OUT/'report_format_failure.txt'), no_model_rerun=True, no_timing_invented=True))
    print('Recovered report/run metadata; all7scientific file hashes unchanged')


if __name__ == '__main__': main()
