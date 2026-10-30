"""Plan and validate a NEW manual study; never fetches labels or alters old freezes."""
import argparse,json
from datetime import datetime,timedelta,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from festival_feature_design import ROOT,sha,dump

OUT=ROOT/'results/rolling_confirmation_plan_v1'
STATES=['Delhi','Karnataka','Maharashtra']
LEADS=[1,7,14]
ARMS=['calendar','zero5','day5','pooled_day5','window5','pooled_window5','placebo_day5','placebo_window5']
MODELS=['ridge_fixed10','tree_leaf20_fixed','tree_leaf2_fixed','sarimax_fixed','chronos','timesfm']


def schedule():
    first=datetime(2026,11,16,9,tzinfo=timezone.utc)
    return [first+timedelta(days=7*k) for k in range(52)]


def target_contract(issued):
    issued=issued.astimezone(ZoneInfo('Asia/Kolkata'))
    day=issued.date()
    cutoff=day-timedelta(days=2)
    # Model origin is cutoff+1; decision lead k maps to model step k+2.
    return dict(context_last_date=cutoff.isoformat(),model_origin=(cutoff+timedelta(days=1)).isoformat(),
        model_horizon=16,targets={str(k):(day+timedelta(days=k)).isoformat() for k in LEADS},
        model_steps={str(k):k+2 for k in LEADS})


def validate_manifest(manifest,planned):
    actual=datetime.fromisoformat(manifest['issued_utc'])
    if actual.tzinfo is None:raise ValueError('Issuance must include timezone')
    if not planned<=actual<=planned+timedelta(minutes=59):raise ValueError('Late/early issuance: record a miss, never backdate')
    expected=target_contract(planned)
    if manifest['contract']!=expected:raise ValueError('Decision leads/availability bridge differ')
    if manifest['units']!='GWh':raise ValueError('Target is supplied energy inGWh')
    if manifest.get('workflow_enabled') is not False:raise ValueError('This registration authorizes manual execution only')
    if manifest.get('calendar_complete') is not True:raise ValueError('Missing dated ledger: record unavailable issuance')
    capture=datetime.fromisoformat(manifest['source_captured_utc'])
    if capture.tzinfo is None or not planned<=capture<=actual:raise ValueError('Source not captured within this issuance')
    if not manifest.get('source_sha256') or not manifest.get('calendar_sha256'):raise ValueError('Missing provenance hash')
    configs={(r['model'],r['arm'],r['state'],r['decision_lead']) for r in manifest['rows']}
    wanted={(m,a,s,k) for m in MODELS for a in ARMS for s in STATES for k in LEADS}
    if configs!=wanted or len(manifest['rows'])!=len(wanted):raise ValueError('Incomplete/duplicated configuration matrix')
    for r in manifest['rows']:
        if r['date']!=expected['targets'][str(r['decision_lead'])] or r['model_step']!=r['decision_lead']+2:raise ValueError('Incorrect decision date/model step')
        if r['context_last_date']!=expected['context_last_date']:raise ValueError('Availability cutoff differs')
    return True


def prepare():
    if OUT.exists():raise FileExistsError('Preserve this plan; version amendments')
    OUT.mkdir()
    entries=[dict(planned_utc=t.isoformat(),**target_contract(t)) for t in schedule()]
    dump(OUT/'schedule.json',entries)
    dump(OUT/'protocol.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),
        status='Future manual study PLAN/contract only; not activated, no forecasts or source captures issued. Existing workflow stays paused.',
        scientific_question='Prospective persistence/failure of typed versus pooled sparse-event representation under an explicit publication-availability bridge.',
        first_issuance=entries[0]['planned_utc'],last_issuance=entries[-1]['planned_utc'],issuances=52,
        schedule='EveryMonday09:00UTC,16November2026–8November2027; actual publication no later09:59UTC. Missed/late/incomplete runs are recorded and never backdated/replaced by hindsight forecasts.',
        availability='At each decision dateD inAsia/Kolkata, use only source labels throughD-2.730calendar-day context endingD-2; causal history fill allowed but score only recorded labels. Models forecast16steps fromD-1; decision leads1/7/14 targetD+1/D+7/D+14, corresponding model steps3/9/16. This differs explicitly from ideal-lag historical leads; no past-day lead1 score.',
        models=MODELS,arms=ARMS,states=STATES,decision_leads=LEADS,model_steps=[3,9,16],
        weights='Exact unchanged pinned Chronos2 andTimesFM3 identities from existing audits; no new checkpoint/fine-tuning or outcome-selected configuration. Context730; native quantiles retained.',
        local_budgets='Refit everyissuance on available730calendar days. Rich27history+13calendar+declaredextra. Ridgealpha10; deterministic float32tree7leaves/200estimators/learning_rate.05/L2=10, minleaf20and2reported separately; fixed SARIMAX(1,0,0)x(1,0,0,7), no trend. Direct local regressions use actual model leads3/9/16, not historical1/7/14. No prospective hyperparameter search.',
        calendar='Before activation, complete state-scoped named calendar and placebo ledger for every used2024–2027context/forecast date, with primary document and notice timestamp. Annual-as-issued definition; retain both declared main/subsidiary dates. Register dated amendments before issuance, hash full used ledger perissuance, never alter past covariates. Missing futureyear coverage blocks issuance rather than silently assigningzero. No assertion allamendments/humansignoffcomplete.',
        data='SameIndianprimarylineage, so this is prospective, NOT source-independent. Eachactualinputsnapshot/time/hash archived asobserved. Source permission/report-day/unit/revision issues must be disclosed; publication-vintage tracking does not resolve historical imputation.',
        outputs='Before eligible targets, write append-only points/nativequantiles, actual issuancetime, input/model/package/datehashes, support/failure logs; normalGitpush and remotecommit verification. Preserve failedfits and missedissuances; no favourable-case intersection or rescheduled hindsightissue.',
        scoring='Separate collector implementation required before activation: after full14day targetperiod, preserve first complete actual snapshot with provenance. Score exact issued cases, bothmodels/locals/allarms, ordinarydays and datedfamilywindows; sharedsourcevintage, fixedpreyearweeklyscale. Native80coverage/width/pinball/WIS, crossingsunmodified. No selection on errors or calibration retuning. FirstforecastGitblob guards and actual timestamp checks mandatory.',
        dependence='Weekly overlappinghorizons and3states share events. Report perissuance/state/family/year cases; use event/series blocks only when enough independent clusters, otherwise descriptive contrasts. Onefutureeventyear does not create manyindependent annual events.',
        prerequisites=['dated2026–2027ledger and final target/reportday/unit/source terms audit',
            'model runner plus source capture/score adapters implemented and fixturetested underthisavailabilitybridge',
            'actualmanualissuance atscheduledfuturetime with firstGitcommit/time guards; contractvalidator alone is not an operational runner'],
        external_gates='Humanreview, rightsholderresponse and futureobservations are not created by thisplan.',
        input_hashes={f:sha(ROOT/f) for f in ['src/rolling_confirmation_plan.py','src/test_rolling_confirmation_plan.py']},
        schedule_sha256=sha(OUT/'schedule.json')))
    (OUT/'README.md').write_text('''# New rolling confirmation plan — not activated

52weekly decisions are specified from16November2026. This leaves the original29October-origin forecasts, interval annex, first-public-commit guards and disabled workflow unchanged. No current/future source retrieval, new forecast issuance or background mechanism is created by this plan.

The availability bridge is explicit: at decision dateD use supplied-energy observations only throughD-2. Future decision leads1/7/14 therefore map to model steps3/9/16, forecastingD+1/D+7/D+14. A historical ideal-availability lead1 comparison cannot silently stand in for that operational task.52overlappingweeks also do not mean52independent festival events.

The six model variants and all eightfeaturearms are fixed before futureoutcomes. Calendar coverage, input/source capture, full runner/scorer adapters and firstGitcommit/time guards remain prerequisites. The included validator tests a manifest contract; it is not an end-to-end operational pipeline. Missingcoverage/lateissuance is recorded, never filled using laterdata or backdatedforecasts. No date-dependentlabel collection is attempted here.

See protocol.json and schedule.json for exact rules/limits. Externalrights/humanreview and actuallaterobservations remain open. No automaticworkflowactivation.
''')
    print('Registered52manual future decisions; statusPLAN_ONLY, no activation/forecast')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','status'])
    if p.parse_args().action=='prepare':prepare()
    else:print('PLAN_ONLY: no scheduler, no new forecast, original automation remains paused')
