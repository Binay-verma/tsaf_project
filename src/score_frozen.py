"""Score the immutable prospective episode only after outcomes have occurred."""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]

FROZEN = ROOT/'results/prospective_20261030_v1'


def score_frame(predictions, actuals, now):
    d = predictions[predictions.prospective_eligible.eq(True)].copy()
    last = pd.to_datetime(d.date).max().date()
    if now.date() <= last:
        raise ValueError('The full eligible target period has not ended; no prospective score is available')
    if actuals.index.has_duplicates:
        raise ValueError('Duplicate actual dates require source reconciliation')
    d['actual'] = [actuals.at[pd.Timestamp(row.date), row.state]
                   if pd.Timestamp(row.date) in actuals.index else np.nan for row in d.itertuples()]
    if not np.isfinite(d.actual).all() or not d.actual.gt(0).all():
        raise ValueError('Missing/nonpositive actuals: preserve the frozen cases; do not impute or silently drop them')
    d['absolute_error'] = abs(d.actual-d.prediction)
    d['scaled_error'] = d.absolute_error/d.mase_scale
    per_state = d.groupby(['model', 'state']).agg(MAE_GWh=('absolute_error', 'mean'),
        MASE=('scaled_error', 'mean'), n=('actual', 'size')).reset_index()
    macro = per_state.groupby('model').MASE.mean().reset_index()
    q = d[d.model.str.startswith('timesfm3_')].copy()
    q['coverage80'] = ((q.actual >= q.q01) & (q.actual <= q.q09)).astype(float)
    q['scaled_width80'] = (q.q09-q.q01)/q.mase_scale
    losses = []
    for i in range(1, 10):
        error = q.actual-q[f'q{i:02d}']
        losses.append(np.maximum(i/10*error, (i/10-1)*error)/q.mase_scale)
    q['scaled_mean_pinball'] = np.mean(losses, axis=0)
    quantiles = q.groupby(['model', 'state'])[
        ['coverage80', 'scaled_width80', 'scaled_mean_pinball']].mean().reset_index()
    return d, per_state, macro, quantiles


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--actuals', required=True, type=Path,
                        help='Audited frozen CSV: date,Karnataka,Delhi,Maharashtra; recorded GWh labels')
    parser.add_argument('--source-url', required=True)
    parser.add_argument('--retrieved-utc', required=True, help='Actual first retrieval timestamp with timezone')
    parser.add_argument('--out', required=True, type=Path, help='A new scoring directory; never forecast directory')
    args = parser.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    freeze = json.loads((FROZEN/'freeze.json').read_text())
    path = FROZEN/'predictions.csv'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == freeze['predictions_sha256']
    retrieved = dt.datetime.fromisoformat(args.retrieved_utc.replace('Z', '+00:00'))
    if retrieved.tzinfo is None or retrieved > now:
        raise ValueError('A real, past, timezone-aware retrieval timestamp is required')
    retrieved = retrieved.astimezone(dt.timezone.utc)
    if retrieved.date() <= dt.date(2026, 11, 11):
        raise ValueError('Acquire the completed outcome snapshot after the target period ends')
    if args.out.exists():
        raise FileExistsError('Use a new scoring directory; never overwrite evidence')
    actuals = pd.read_csv(args.actuals, index_col=0, parse_dates=True)
    d, states, macro, quantiles = score_frame(pd.read_csv(path), actuals, now)
    args.out.mkdir(parents=True)
    d.to_csv(args.out/'scored_predictions.csv', index=False)
    states.to_csv(args.out/'state_metrics.csv', index=False)
    macro.to_csv(args.out/'macro_metrics.csv', index=False)
    quantiles.to_csv(args.out/'native_quantile_metrics.csv', index=False)
    metadata = dict(scored_utc=now.isoformat(), actuals_retrieved_utc=retrieved.isoformat(),
        source_url=args.source_url, actuals_sha256=hashlib.sha256(args.actuals.read_bytes()).hexdigest(),
        frozen_predictions_sha256=freeze['predictions_sha256'], scored_rows=len(d),
        warning='One shared-source forecast episode; no retuning, independent-source or broad significance claim')
    (args.out/'audit.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print(macro.to_string(index=False))


if __name__ == '__main__':
    main()
