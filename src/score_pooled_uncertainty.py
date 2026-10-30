"""Common native quantile/80% interval audit; no calibration or repair."""
import argparse
from datetime import datetime, timezone
import json
import numpy as np
import pandas as pd
from pooled_festival_experiment import OUT
from festival_feature_design import sha, dump
from report_multifestival import markdown


def prepare():
    path = OUT/'probabilistic_protocol.json'
    if path.exists():
        raise FileExistsError('Preserve fixed probability scoring protocol')
    dump(path, dict(created_utc=datetime.now(timezone.utc).isoformat(),
        status='Exploratory secondary analysis fixed while pooled inference is running, before pooled score tables. Prior historical point and native-crossing evidence already inspected. Not original external preregistration.',
        models=['chronos', 'timesfm'], cohorts=['event', 'non_event'],
        arms=['calendar', 'day5', 'window5', 'pooled_day1', 'pooled_day5', 'pooled_window1', 'pooled_window5', 'zero1'],
        quantiles=[i/10 for i in range(1, 10)],
        pinball='Mean over9common native levels: max(tau*(actual-q),(tau-1)*(actual-q)), divided by unchanged pre-year weekly-difference scale. No interpolation.',
        interval='Native q0.1/q0.9 central80percent interval; width, inclusive coverage, lower/upper miss rates, median absolute error and interval score: width+10*(lower-actual)whenbelow+10*(actual-upper)whenabove.',
        wis='One-interval WIS=(0.5*abs(actual-native_median)+0.1*interval_score)/1.5, scaled by same denominator. Not a full19quantile or9quantile WIS.',
        invalid='Preserve every output. Record common-grid and all-native adjacent crossings. If lower>upper, coverage,width,interval_score,WIS are undefined for that case and the aggregate is undefined rather than silently dropping invalid intervals. Pinball remains defined per marginal quantile. No sorting/clipping, isotonic correction or calibration.',
        aggregation='Identical72cases/model/arm/cohort, individual leads1/7/14. Equal states within year, years within family, families overall. Report all arms/models/leads/families/years. No day-independent binomial/significance claims.',
        limits='Native distributions are uncalibrated. Only24date targets/lead in each historical cohort, correlated states and two years. This is empirical bounded coverage, not reliable calibration, proper joint distribution validation, all-day performance or independent review.',
        scoring_source_sha256=sha(__file__), registration_sha256=sha(OUT/'registration.json')))
    print('FROZEN common9quantiles/native80percent/one-intervalWIS; no adjustment')


def score():
    p = json.loads((OUT/'probabilistic_protocol.json').read_text())
    assert sha(__file__) == p['scoring_source_sha256']
    assert sha(OUT/'registration.json') == p['registration_sha256']
    if (OUT/'probabilistic_run.json').exists():
        raise FileExistsError('Preserve completed probability analysis')
    summaries = {}
    for cohort in p['cohorts']:
        out = OUT/cohort
        d = pd.read_csv(out/'predictions_primary.csv')
        d = d[d.model.isin(p['models'])].copy()
        assert len(d) == 2*8*72
        qcols = [f'q_{i*100:03d}' for i in range(1, 10)]
        q = d[qcols].to_numpy(); y = d.actual.to_numpy()
        assert np.isfinite(q).all()
        residual = y[:, None]-q
        levels = np.arange(1, 10)/10.
        losses = np.maximum(levels*residual, (levels-1)*residual)
        d['scaled_mean_pinball'] = losses.mean(axis=1)/d.mase_scale
        d['common_adjacent_crossings'] = (np.diff(q, axis=1) < 0).sum(axis=1)
        low, median, high = q[:, 0], q[:, 4], q[:, 8]
        invalid = low > high
        d['invalid80'] = invalid
        width = high-low
        interval_score = width+10*np.maximum(low-y, 0)+10*np.maximum(y-high, 0)
        d['coverage80'] = np.where(invalid, np.nan, ((low <= y) & (y <= high)).astype(float))
        d['below80'] = np.where(invalid, np.nan, (y < low).astype(float))
        d['above80'] = np.where(invalid, np.nan, (y > high).astype(float))
        d['width80_GWh'] = np.where(invalid, np.nan, width)
        d['scaled_width80'] = d.width80_GWh/d.mase_scale
        d['scaled_interval_score80'] = np.where(invalid, np.nan, interval_score)/d.mase_scale
        d['scaled_WIS80_median'] = np.where(invalid, np.nan, (.5*abs(y-median)+.1*interval_score)/1.5)/d.mase_scale
        metrics = ['scaled_mean_pinball', 'coverage80', 'below80', 'above80', 'scaled_width80', 'scaled_interval_score80', 'scaled_WIS80_median']
        keys = ['family', 'model', 'arm', 'state', 'year', 'horizon']
        details = d[keys+['origin', 'date', 'actual', 'mase_scale', 'width80_GWh', 'invalid80', 'common_adjacent_crossings']+qcols+metrics]
        details.to_csv(out/'native_uncertainty_cases.csv', index=False)
        cells = d.groupby(keys)[metrics+['width80_GWh']].mean().reset_index()
        cells.to_csv(out/'native_uncertainty_state_year.csv', index=False)
        # Explicit propagation: pandas mean would otherwise omit invalid intervals.
        interval_metrics = [k for k in metrics if k != 'scaled_mean_pinball']
        bad = d.groupby(['model', 'arm', 'horizon']).invalid80.any()
        years = cells.groupby(['family', 'model', 'arm', 'year', 'horizon'])[metrics].mean().reset_index()
        families = years.groupby(['family', 'model', 'arm', 'horizon'])[metrics].mean().reset_index()
        for (model, arm, h), is_bad in bad.items():
            if is_bad:
                # Do not imply any partially averaged valid-interval result is complete.
                mask = families.model.eq(model) & families.arm.eq(arm) & families.horizon.eq(h)
                families.loc[mask, interval_metrics] = np.nan
        families.to_csv(out/'native_uncertainty_festival.csv', index=False)
        balanced = families.groupby(['model', 'arm', 'horizon'])[metrics].mean().reset_index()
        for (model, arm, h), is_bad in bad.items():
            if is_bad:
                balanced.loc[balanced.model.eq(model) & balanced.arm.eq(arm) & balanced.horizon.eq(h), interval_metrics] = np.nan
        balanced.to_csv(out/'native_uncertainty_balanced.csv', index=False)
        lines = ['# Native uncertainty — '+cohort, '', p['status'], '',
            'Common native0.1–0.9quantiles only.80%intervals are uncalibrated. Lower pinball/WIS is better; coverage must be interpreted with width/score. WIS here uses one80%interval plus the native median. These are not the separate calibrated90%residual intervals.', '']
        for h in [1, 7, 14]:
            lines += ['## Individual lead '+str(h), '', markdown(balanced[balanced.horizon.eq(h)][['model', 'arm']+metrics].round(5)), '']
        lines += [p['limits'], '', 'No marginal-quantile sorting, clipping, recalibration or post-hoc arm selection. Invalid endpoints remain explicit. See case/state-year/family outputs and the separate input audit for all-native crossings.']
        (out/'NATIVE_UNCERTAINTY.md').write_text('\n'.join(lines)+'\n')
        summaries[cohort] = dict(rows=len(d), invalid80=int(invalid.sum()), common_adjacent_crossing_pairs=int(d.common_adjacent_crossings.sum()),
            combined_predictions_sha256=sha(out/'predictions_primary.csv'), scored_cases_sha256=sha(out/'native_uncertainty_cases.csv'))
    dump(OUT/'probabilistic_run.json', dict(status='completed', completed_utc=datetime.now(timezone.utc).isoformat(),
        protocol_sha256=sha(OUT/'probabilistic_protocol.json'), cohorts=summaries))
    print(json.dumps(summaries, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['prepare', 'score'])
    prepare() if parser.parse_args().action == 'prepare' else score()
