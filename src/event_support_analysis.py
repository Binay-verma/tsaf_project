"""Prespecified past-only support/response moderators of existing contrasts.

No new forecasts, model selection or causal effects. Reuses the complete
document-aligned cohort, including negative and undefined associations.
"""
import argparse
from collections import deque
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pandas as pd

from forecasting import ROOT
from festival_feature_design import KEY, FAMILIES, sha, dump

OUT = ROOT/'results/event_support_v1'
RECENTER = ROOT/'results/calendar_recenter_v1'
MODELS = ['ridge', 'lightgbm', 'lightgbm_capacity2', 'sarimax', 'chronos', 'timesfm']
METRICS = ['own_support_days', 'own_support_ratio', 'own_prior_year_support_days',
           'heterogeneity_scaled', 'target_flag_active', 'future_own_support_days']


def register():
    if OUT.exists():
        raise FileExistsError('Preserve earlier moderator analysis')
    names = ['src/event_support_analysis.py', 'src/audit_event_support.py',
             'src/complete_event_support.py', 'src/test_event_support.py',
             'src/festival_feature_design.py', 'src/forecasting.py',
             'data/external/latest_state_energy_GWh.csv',
             'results/calendar_recenter_v1/event_cases_recentered.csv',
             'results/calendar_semantics_v2/anchors_2022_2025.csv']
    OUT.mkdir(parents=True)
    dump(OUT/'protocol.json', dict(created_utc=datetime.now(timezone.utc).isoformat(),
        status='Exploratory descriptive analysis registered after original-calendar aggregates were inspected, BEFORE computing these moderator values/associations or complete corrected foundation aggregates. No independent preregistration/causal mechanism claim.',
        question='Do typed-minus-pooled forecast errors vary with available recorded family support and differences in past family residual means? Lower support/more homogeneous responses are hypothesised to favour pooling; retain the contrary/null/undefined findings.',
        cohort='All528document-aligned/recentered eventcases x6variants x2day/window representations=6336existing pairedcontrasts. No new forecasts, selectedcases, fittedpredictor or futurearmchoice. Foundationmodelsprimary, fourlocalsdescriptive; neverpoolmodelsasindependentreplications.',
        context='For everycase use ONLY730calendar days strictlybefore itsorigin. Positive finite recordedlabels only; no labelimputation. Sourcecurrentvintage/exploratory. Sameinput-context information for moderators; this doesnot equalise localmodel totaltraining/history budgets.',
        support='Own/anyfamily active recordedcontext days for day/windowunionflags; theirratio; ownprior-year/current-year support separately. Subsidiarydates/windowscountsupportDAYS, not independentoccurrences. Querytargetflag and14future-knowncalendar active-day counts use datesonly.',
        response='Sharedordinarybaseline: fourpreceding positive recorded SAMEweekday labels withinthiscontext, excludingALLnamedfamily+-3daywindows. If fewerthan4, residualundefined. Compute labelminusbaseline dividedbyfixedpreyearweeklyscale. Eachsupportedfamily meanuses itsday/windowdates withdefinedresiduals. Heterogeneity=populationRMS deviation ofsupportedfamilymeans fromtheirequalfamilymean, requiring>=2supportedfamilies. No inventedzero/unseen-effect imputation; observedproxy, not learned/causalimpact.',
        estimand='Typedminuspooled absoluteerror dividedby samefixedscale; positive favours pooling. Average withinmodel/representation/family/state/year/modellead cell, sameasregisteredpointcells. All6moderators, PearsonandSpearman associations permodel/representation/lead, bothyears and leaveonefamilyout. ForassociationsONLY roundbothcellvariables to8decimalplaces todefine numericalties; retainrawcells. Minimum3definedcells/nonzerovariance; otherwiseundefined. No significance/IIDtests, thresholdsearch, regressionselection or causalattribution.',
        limitations='Only24family/state/yeargroups, twoeventyears and relatedstates; support/heterogeneity confoundstate/family/year/within-eventposition. Current-yearhistory maycontainearlierresponses fromthe SAMEepisode; recordedseparately, not unseen-eventevidence. ANYundefinedmoderator withinacell makes thatcellmoderatorundefined; keepALLforecastdeltas. Missingmoderators affect ONLYassociation availability, neverforecastcohort/scoring. No allmodel correlation/precision claim.',
        source_hashes={name: sha(ROOT/name) for name in names}))
    print('Registered1056past-onlymoderatorrows and6336reusedcontrasts before moderator outputs')


def flags(dates, ledger, state, representation):
    values = []
    for family in FAMILIES:
        roots = ledger[ledger.state.eq(state)&ledger.family.eq(family)].date
        active = roots if representation == 'day' else [day for root in roots for day in pd.date_range(root-pd.Timedelta(days=3), root+pd.Timedelta(days=3))]
        values.append(dates.isin(active))
    return np.asarray(values, dtype=bool)


def past_residuals(values, weekdays, excluded, scale):
    """Only earlier non-event records enter each weekday baseline."""
    histories = [deque(maxlen=4) for _ in range(7)]
    result = np.full(len(values), np.nan)
    for i, (value, weekday, skip) in enumerate(zip(values, weekdays, excluded)):
        if not np.isfinite(value) or value <= 0:
            continue
        if len(histories[weekday]) == 4:
            result[i] = (value-float(np.mean(histories[weekday])))/scale
        if not skip:
            histories[weekday].append(float(value))
    return result


def prepare():
    protocol = json.loads((OUT/'protocol.json').read_text())
    for name, expected in protocol['source_hashes'].items():
        assert sha(ROOT/name) == expected, name
    if (OUT/'moderators.csv').exists():
        raise FileExistsError('Preserve existing moderator values')
    data = pd.read_csv(ROOT/'data/external/latest_state_energy_GWh.csv', index_col=0, parse_dates=True).asfreq('D')
    ledger = pd.read_csv(ROOT/'results/calendar_semantics_v2/anchors_2022_2025.csv', parse_dates=['date'])
    cases = pd.read_csv(RECENTER/'event_cases_recentered.csv', parse_dates=['origin', 'date'])
    assert len(cases) == 528
    cache = {}
    rows = []
    for case in cases.itertuples(index=False):
        end = pd.Timestamp(f'{case.year-1}-12-31')
        y = data[case.state].loc[end-pd.Timedelta(days=729):end]
        scale = float((y-y.shift(7)).abs().mean())
        for representation in ['day', 'window']:
            key = case.state, case.origin, case.year, representation
            if key not in cache:
                dates = pd.date_range(case.origin-pd.Timedelta(days=730), periods=730)
                observed = data[case.state].reindex(dates).to_numpy()
                good = np.isfinite(observed)&(observed > 0)
                active = flags(dates, ledger, case.state, representation)
                excluded = flags(dates, ledger, case.state, 'window').any(axis=0)
                residuals = past_residuals(observed, dates.dayofweek.to_numpy(), excluded, scale)
                means = [float(np.mean(residuals[mask&np.isfinite(residuals)]))
                         for mask in active if np.any(mask&np.isfinite(residuals))]
                heterogeneity = float(np.std(means, ddof=0)) if len(means) >= 2 else np.nan
                future = pd.date_range(case.origin, periods=14)
                cache[key] = dict(dates=dates, good=good, active=active, scale=scale,
                    heterogeneity=heterogeneity, response_families=len(means),
                    future=flags(future, ledger, case.state, representation))
            a = cache[key]
            index = FAMILIES.index(case.family)
            own = a['active'][index]&a['good']
            pooled = a['active'].any(axis=0)&a['good']
            target = flags(pd.DatetimeIndex([case.date]), ledger, case.state, representation)
            row = case._asdict()
            for name in ['origin', 'date']:
                row[name] = str(pd.Timestamp(row[name]).date())
            row.update(representation=representation,
                own_support_days=int(own.sum()), pooled_support_days=int(pooled.sum()),
                own_support_ratio=float(own.sum()/pooled.sum()) if pooled.sum() else np.nan,
                own_prior_year_support_days=int((own&(a['dates'].year < case.year)).sum()),
                own_current_year_support_days=int((own&(a['dates'].year == case.year)).sum()),
                heterogeneity_scaled=a['heterogeneity'], supported_response_families=a['response_families'],
                target_flag_active=int(target[index, 0]), future_own_support_days=int(a['future'][index].sum()),
                recorded_context_labels=int(a['good'].sum()), max_context_label=str(a['dates'][a['good']].max().date()),
                mase_scale=a['scale'])
            assert pd.Timestamp(row['max_context_label']) < case.origin
            rows.append(row)
    d = pd.DataFrame(rows)
    assert len(d) == 1056 and not d.duplicated(KEY+['representation']).any()
    d.to_csv(OUT/'moderators.csv', index=False)
    dump(OUT/'moderator_build.json', dict(completed_utc=datetime.now(timezone.utc).isoformat(),
        rows=1056, cached_contexts=len(cache), protocol_sha256=sha(OUT/'protocol.json'),
        moderators_sha256=sha(OUT/'moderators.csv'), future_labels_used=False))
    print('Complete1056past-onlymoderatorrows; no forecasterrors read')


def association(x, y):
    good = np.isfinite(x)&np.isfinite(y)
    x = pd.Series([round(float(value), 8) for value in np.asarray(x)[good]])
    y = pd.Series([round(float(value), 8) for value in np.asarray(y)[good]])
    if len(x) < 3 or x.nunique() < 2 or y.nunique() < 2:
        return len(x), np.nan, np.nan
    return len(x), float(x.corr(y)), float(x.rank(method='average').corr(y.rank(method='average')))


def analyze():
    protocol = json.loads((OUT/'protocol.json').read_text())
    for name, expected in protocol['source_hashes'].items():
        assert sha(ROOT/name) == expected, name
    if (OUT/'run.json').exists():
        raise FileExistsError('Preserve completed analysis')
    assert json.loads((RECENTER/'analysis/independent_audit.json').read_text())['status'] == 'pass'
    build = json.loads((OUT/'moderator_build.json').read_text())
    assert sha(OUT/'moderators.csv') == build['moderators_sha256']
    assert sha(OUT/'protocol.json') == build['protocol_sha256']
    point_path = RECENTER/'analysis/breadth/event_window/predictions_compared.csv'
    parent = json.loads((RECENTER/'analysis/run.json').read_text())
    assert sha(point_path) == parent['cohorts']['breadth/event_window']['predictions_sha256']
    d = pd.read_csv(point_path)
    d = d[d.version.eq('document_aligned')]
    moderators = pd.read_csv(OUT/'moderators.csv')
    chunks = []
    for representation in ['day', 'window']:
        arm, reference = representation+'5', 'pooled_'+representation+'5'
        left = d[d.arm.eq(arm)].copy()
        right = d[d.arm.eq(reference)]
        a = left.merge(right[KEY+['model', 'prediction', 'actual', 'mase_scale']],
            on=KEY+['model'], suffixes=('_typed', '_pooled'), validate='one_to_one')
        assert len(a) == 528*6 and (a.actual_typed == a.actual_pooled).all()
        assert (a.mase_scale_typed == a.mase_scale_pooled).all()
        a['typed_minus_pooled_MASE'] = (abs(a.prediction_typed-a.actual_typed)-abs(a.prediction_pooled-a.actual_typed))/a.mase_scale_typed
        a['representation'] = representation
        a = a.merge(moderators, on=KEY+['representation'], validate='many_to_one', suffixes=('', '_moderator'))
        assert len(a) == 528*6
        chunks.append(a[KEY+['model', 'representation', 'typed_minus_pooled_MASE']+METRICS])
    paired = pd.concat(chunks, ignore_index=True)
    assert len(paired) == 6336
    paired.to_csv(OUT/'paired_cases.csv', index=False)
    groups = ['model', 'representation', 'family', 'state', 'year', 'horizon']
    grouped = paired.groupby(groups)
    cells = grouped[['typed_minus_pooled_MASE']+METRICS].mean()
    for name in METRICS:
        invalid = grouped[name].apply(lambda values: values.isna().any())
        cells.loc[invalid, name] = np.nan
    cells = cells.reset_index()
    assert len(cells) == 864
    cells.to_csv(OUT/'cells.csv', index=False)
    rows = []
    for (model, representation, horizon), group in cells.groupby(['model', 'representation', 'horizon']):
        scopes = [('all', group)]+[(f'year_{year}', group[group.year.eq(year)]) for year in [2024, 2025]]
        scopes += [('omit_'+family, group[~group.family.eq(family)]) for family in FAMILIES]
        for scope, part in scopes:
            for metric in METRICS:
                n, pearson, spearman = association(part[metric].to_numpy(), part.typed_minus_pooled_MASE.to_numpy())
                rows.append(dict(model=model, representation=representation, horizon=int(horizon),
                    scope=scope, moderator=metric, total_cells=len(part), defined_cells=n,
                    pearson=pearson, spearman=spearman))
    result = pd.DataFrame(rows)
    assert len(result) == 1728
    result.to_csv(OUT/'associations.csv', index=False)
    dump(OUT/'run.json', dict(completed_utc=datetime.now(timezone.utc).isoformat(),
        paired_rows=6336, cells=864, associations=1728, new_forecasts=0,
        point_source_sha256=sha(RECENTER/'analysis/breadth/event_window/predictions_compared.csv'),
        moderator_source_sha256=sha(OUT/'moderators.csv'), protocol_sha256=sha(OUT/'protocol.json')))
    print('Complete6336reusedpairs/864cells/1728associations; separateauditrequired')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['register', 'prepare', 'analyze'])
    action = parser.parse_args().action
    {'register': register, 'prepare': prepare, 'analyze': analyze}[action]()
