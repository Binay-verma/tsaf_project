"""Summarize completed audited studies; no new inference or model selection."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import pandas as pd
from report_multifestival import markdown

ROOT = Path(__file__).resolve().parents[1]


def main():
    destination = ROOT/'COMPLETE_RESULTS_20261031.md'
    if destination.exists():
        raise FileExistsError('Preserve prior report')
    audits = [
        'results/feature_breadth_v1/independent_audit.json',
        'results/calendar_encoding_v1/independent_audit.json',
        'results/neso_replication_v1/analysis/independent_audit.json',
        'results/calendar_semantics_v2/analysis/independent_audit.json',
        'results/calendar_recenter_recovery_v1/analysis/independent_audit.json',
        'results/calendar_recenter_recovery_v1/analysis/contrasts/audit.json',
        'results/mta_holiday_recovery_v1/analysis/independent_audit.json',
        'results/event_support_v1/independent_audit.json',
        'review/clean_mta_v1/comparison.json', 'review/clean_extended_v1/comparison.json',
        'results/prospective_chronos_20261031_v1/independent_audit.json',
        'manuscript/integrated_review_v4/independent_reporting_audit.json']
    inputs = {}

    def record(name):
        path = ROOT/name
        inputs[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        return path

    for name in audits:
        assert json.loads(record(name).read_text())['status'] == 'pass', name

    def table(name):
        path = record(f'manuscript/integrated_review_v4/supplement/{name}.csv')
        return markdown(pd.read_csv(path).round(5))

    name = 'results/calendar_recenter_recovery_v1/analysis/encoding/event_window/metrics_balanced.csv'
    pure = pd.read_csv(record(name))
    pure = pure[pure.version.eq('document_aligned')]
    pure = pure.pivot(index='arm', columns=['model', 'horizon'], values='MASE')
    pure = pure.reindex(['history', 'zero1', 'ordinal', 'onehot', 'cyclic', 'te_weekday',
        'te_sunday', 'te_holiday', 'te_joint', 'te_separate', 'calendar'])
    pure.columns = [f'{model} lead {lead}' for model, lead in pure.columns]
    text = '''# Completed research loop — 31 October 2026

All registered historical provider lanes and separate audits are complete. This does not close every journal gate. Outcomes are exploratory; more related forecast rows do not create independent events. The document-aligned, recentered Indian panel is the current main analysis. Original results and failures remain preserved.

## Corrected Indian festival windows

528 common target/lead cases across three related states, two years and five named families. Lower MASE is better. Lead 1 below; all eight arms and three leads remain in the source tables. Five substantive representations are displayed; zero and weekday-placebo controls are retained.

'''+table('india_event')+'''

SARIMAX typed-day and TimesFM pooled-day are close here. No significance or universal winner follows. Typed/pooled contrasts match the five-channel event budget. Local and foundation adaptation/history policies differ, so model rankings are not architecture-only effects.

## Closest calendar-encoding adaptations

Every registered encoding on the same corrected Indian festival cases, all three leads. Target means use only preceding recorded context, never forecast labels. This daily adaptation differs from the closest paper's hourly experiment. Channel counts differ: one/two/three/eight versus 13 for calendar. The smallest displayed value is not a selected recommendation or proof of equal-information superiority.

'''+markdown(pure.reset_index().round(5))+'''

## Independent-source NYC holidays

Two occurrences and two related transit modes in one city, 84 event cases. Decision lead 1 uses actual model step 8 under the seven-day observation buffer. Units are million estimated rides. Cross-dataset MASE levels do not imply equal task difficulty.

'''+table('mta_event')+'''

Chronos benefits from pooled-day flags here, while TimesFM favours typed-day flags and SARIMAX pooling worsens its calendar baseline. All leads, ordinary cases and controls are retained. This is revised-vintage retrospective evidence, not independent-city or prospective confirmation.

## Different electricity source and availability sensitivity

NESO ordinary September targets at decision lead 1: ideal actual model step 1 versus lag-21 actual model step 22. No holiday targets occur. Delay need not monotonically worsen realised error in this small sample; regressions also change lead-dependent features/fits.

'''+table('neso')+'''

## Prespecified past-support diagnostics

The analysis reuses 6,336 typed-minus-pooled case contrasts, 864 family/state/year/lead cells and 1,728 descriptive association records. The table is the declared day/lead-1/all-scope slice; all other scopes are retained. Positive forecast contrasts favour pooling. The 24 available cells are not independent replications. Mixed residual-response associations do not establish a general mechanism or causal effect.

'''+table('support_diagnostics')+'''

## Completed checks and preserved limitations

- Original breadth: 35,712 forecasts. Pure encodings: 14,880 fresh forecasts plus 1,488 reused calendar references. Composed/corrected views are not independent new data.
- Source correction changes one Karnataka named date. Recentring replaces three lead cases for one target date, not three target dates. All 1,092 fresh recenter forecasts and full contrasts pass audit.
- NESO: 4,608 model plus 192 naive rows. NYC: 6,300 model plus 252 naive rows; source/input/calendar/native/scalar audits pass.
- Clean internal runs reproduce all 4,032 NYC local forecasts and 72 validation MAEs exactly, plus comparator/simulation outputs. Same machine; no independent human or complete foundation reimplementation.
- Earlier float64-tree reproduction failure, near-zero float32 feature discrepancy, calendar preflight/interrupted-report/dispatch/schema failures remain preserved. Repairs did not select new cases, parameters, metrics or tolerances using errors.
- New Chronos future competitor: 84 stored/66 eligible full 1–11 November forecasts, actual completion 31 October 05:14:07 IST. First public commit `0e4ab330d6a798545f31476f79c59f55975eb8e3` and observed remote receipt precede eligible dates. No future accuracy exists. Same source/episode/stale context as the older freeze; no festival-feature confirmation.
- Old future and interval blobs are immutable. Manual date/vintage guards and paused automation remain in force. No future actuals were retrieved.

## Next loop and open gates

1. Publish completed artifacts and the integrated review draft after numerical/all-page visual checks. Historical computations above are finished; do not restart them to seek better scores.
2. Complete manual rolling-confirmation source/runner/scorer software and fixtures using its fixed availability bridge and first-commit/time guards. The 52-week study is unactivated; do not issue fake or early forecasts.
3. Verify primary 2026–2027 calendar coverage/amendments before future festival-feature issuance. Secondary pages/failed retrievals do not close this gate. MH2022 retained-excerpt evidence remains incomplete.
4. Obtain real independent scientific review and source-use/report-day clarification. The author is not the independent reviewer; no permission or sign-off is inferred.
5. Wait for actual outcomes, then score every issued configuration on the original first complete actual vintage. Repeated untouched events, rather than one episode or more models, are needed for stronger confirmation.

The proposed contribution is a conditional empirical forecasting lesson, not a new architecture, causal effect, contamination-free claim or IJF acceptance assurance. Exact impact-driven learned-event replication remains unresolved because full settings/code/account-profile data were not identified in examined sources. Author affiliation/email remain blank as requested.

Sources: [integrated draft](manuscript/integrated_review_v4/MANUSCRIPT.md), [corrected breadth](results/calendar_recenter_recovery_v1/analysis/breadth/event_window/metrics_balanced.csv), [corrected pure encodings](results/calendar_recenter_recovery_v1/analysis/encoding/event_window/metrics_balanced.csv), [NYC](results/mta_holiday_recovery_v1/analysis/event_window/metrics_balanced.csv), [NESO](results/neso_replication_v1/analysis/metrics.csv), [all diagnostics](results/event_support_v1/associations.csv).
'''
    destination.write_text(text)
    out = ROOT/'review/completed_loop_20261031_v1'
    out.mkdir(exist_ok=True)
    result = dict(checked_utc=datetime.now(timezone.utc).isoformat(),
        status='listed_registered_historical_lanes_and_internal_audits_complete',
        scope='Completed executable loop, not every external journal gate. No new forecasts or outcome-based selection.',
        inputs=inputs, summary_sha256=hashlib.sha256(text.encode()).hexdigest(),
        builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
