"""Rolling confirmation, timing rule v2 (registered amendment; v1 files are unchanged).

The ONLY change from rolling_execution_v1: activation no longer requires a complete 2024-2027
calendar package up front. Each issuance still requires, via the unchanged
rolling_evidence_v1.calendar_package(), complete primary coverage for every year spanned by
its own 730-day context and targets (+/-3 days), plus the unchanged reviewed source-rights,
units and observation-day evidence. Windows, models, arms, leads, scoring, guards and the
miss rule are exactly v1's. Registered before any rolling issuance or rolling outcome.

Usage: python src/rolling_execution_v2_timing.py {status,issue,receipt,collect,score,miss} --number N
"""
import argparse
import hashlib
import json
from pathlib import Path

import rolling_evidence_v1 as evidence
import rolling_execution_v1 as v1

ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = ROOT/'results/rolling_confirmation_timing_v2/registration.json'


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_v2_registration():
    if not REGISTRATION.exists():
        raise ValueError('Timing rule v2 is not registered')
    reg = json.loads(REGISTRATION.read_text())
    for name, expected in reg['code_sha256'].items():
        if _sha(ROOT/name) != expected:
            raise ValueError('Registered timing-v2 dependency changed:'+name)
    return reg


def prerequisites_v2(number, now):
    """v1.prerequisites without the global 2024-2027 completeness check (v1 lines 65-68)."""
    path = v1.BASE/'activation.json'
    if not path.exists():
        raise ValueError('UNACTIVATED: reviewed source/date/calendar prerequisites missing')
    activation = json.loads(path.read_text())
    if activation['status'] != 'reviewed_prerequisites' or activation['source_units'] != 'GWh' or activation['source_observation_day_confirmed'] is not True:
        raise ValueError('Unresolved source unit/day convention')
    if v1.datetime.fromisoformat(activation['reviewed_utc']) > now:
        raise ValueError('Review is not yet available')
    for key in ['source_rights_evidence', 'source_date_evidence']:
        item = activation[key]
        if v1.sha(v1.within(v1.ROOT, item['file'])) != item['sha256']:
            raise ValueError('Missing/changed reviewed source evidence')
    manifest = v1.within(v1.ROOT, activation['calendar_manifest'])
    if v1.sha(manifest) != activation['calendar_manifest_sha256']:
        raise ValueError('Calendar package changed since review')
    package, anchors, fake = evidence.calendar_package(manifest, number, now)  # per-issuance years enforced here
    return activation, manifest, package, anchors, fake


def run(action, number):
    validate_v2_registration()
    if action == 'issue':
        original = v1.prerequisites
        v1.prerequisites = prerequisites_v2
        try:
            result = v1.issue(number)
        finally:
            v1.prerequisites = original
        evidence.dump(v1.folder_for(number)/'timing_rule_v2.json',
                      dict(registration=str(REGISTRATION.relative_to(ROOT)), registration_sha256=_sha(REGISTRATION)))
        return result
    return getattr(v1, action)(number)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['status', 'issue', 'receipt', 'collect', 'score', 'miss'])
    parser.add_argument('--number', type=int)
    args = parser.parse_args()
    if args.action == 'status':
        validate_v2_registration()
        print('TIMING_V2_REGISTERED_UNACTIVATED: per-issuance calendar coverage; all other v1 prerequisites unchanged')
    else:
        if args.number is None:
            parser.error('--number required')
        out = run(args.action, args.number)
        if out:
            print(out)
