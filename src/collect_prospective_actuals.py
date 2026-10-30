"""Date-gated, idempotent collection/scoring of the already-frozen episode."""
from pathlib import Path
import argparse
import datetime as dt
import gzip
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import urllib.request
import pandas as pd
from score_frozen import ROOT, FROZEN

SOURCE = 'https://robbieandrew.github.io/india/data/POSOCO_data.csv'
METADATA = 'https://robbieandrew.github.io/india/data/POSOCO_metadata.json'
FREEZE_COMMIT = 'cabd5982e1948652b9841d6c31a2380f6f314198'
STATES = ['Karnataka','Delhi','Maharashtra']


def ready(now):
    return now.year == 2026 and now.date() > dt.date(2026,11,11)


def extract(raw, metadata):
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    fields = {f['name']:f for f in metadata['fields']}
    for state in STATES:
        if fields[state+': EnergyMet']['units'] != 'GWh':
            raise ValueError('Unexpected source unit; do not silently convert')
    data = pd.read_csv(io.BytesIO(raw))
    data.index = pd.to_datetime(data.yyyymmdd.astype(str), format='%Y%m%d')
    if data.index.has_duplicates:
        raise ValueError('Duplicate source dates need review')
    targets = pd.date_range('2026-10-31','2026-11-11')
    selected = data.reindex(targets)[[s+': EnergyMet' for s in STATES]].copy()
    selected.columns = STATES
    selected.index.name = 'date'
    if selected.isna().any().any() or not selected.gt(0).all().all():
        return None
    return selected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT/'results/prospective_20261030_scoring_v1')
    parser.add_argument('--github-output', type=Path)
    args = parser.parse_args()
    def output(scored):
        if args.github_output:
            with args.github_output.open('a') as f:
                f.write('scored='+str(scored).lower()+'\n')
    now = dt.datetime.now(dt.timezone.utc)
    if not ready(now):
        output(False)
        print('PENDING: no network request or score before full target period ends; collection limited to2026.')
        return
    if args.out.exists():
        if (args.out/'audit.json').is_file():
            output(False)
            print('ALREADY SCORED: preserve first recorded evaluation; no automatic overwrite.')
            return
        raise FileExistsError('Incomplete/existing output needs manual review')
    rel = 'results/prospective_20261030_v1/predictions.csv'
    original_blob = subprocess.check_output(['git','rev-parse',f'{FREEZE_COMMIT}:{rel}'],cwd=ROOT,text=True).strip()
    current_blob = subprocess.check_output(['git','hash-object',str(FROZEN/'predictions.csv')],cwd=ROOT,text=True).strip()
    if current_blob != original_blob:
        raise ValueError('Forecast differs from original pre-outcome Git commit')
    with urllib.request.urlopen(SOURCE,timeout=60) as response:
        raw = response.read()
    with urllib.request.urlopen(METADATA,timeout=30) as response:
        meta_raw = response.read()
    metadata = json.loads(gzip.decompress(meta_raw) if meta_raw[:2] == b'\x1f\x8b' else meta_raw)
    actuals = extract(raw,metadata)
    if actuals is None:
        output(False)
        print('PENDING: source has incomplete/nonpositive eligible labels; no imputation or score produced.')
        return
    retrieved = dt.datetime.now(dt.timezone.utc).isoformat()
    actual_bytes = actuals.to_csv().encode()
    with tempfile.TemporaryDirectory() as temp:
        csv = Path(temp)/'actuals.csv'
        csv.write_bytes(actual_bytes)
        subprocess.run([sys.executable,str(ROOT/'src/score_frozen.py'),'--actuals',str(csv),
            '--source-url',SOURCE,'--retrieved-utc',retrieved,'--out',str(args.out)],check=True)
    (args.out/'actuals_snapshot.csv').write_bytes(actual_bytes)
    (args.out/'source_metadata_snapshot.json').write_bytes(json.dumps(metadata,indent=2).encode()+b'\n')
    collection = dict(retrieved_utc=retrieved,source_url=SOURCE,metadata_url=METADATA,
        raw_source_sha256=hashlib.sha256(raw).hexdigest(),metadata_sha256=hashlib.sha256(meta_raw).hexdigest(),
        eligible_labels_sha256=hashlib.sha256(actual_bytes).hexdigest(),original_freeze_commit=FREEZE_COMMIT,
        original_forecast_git_blob=original_blob,
        warning='First post-period source snapshot, not certified final/unimputed labels or human scientific approval. Do not retune forecasts on these scores.')
    (args.out/'collection.json').write_text(json.dumps(collection,indent=2)+'\n')
    output(True)
    print('SCORED: frozen forecasts preserved; eligible actuals and provenance retained.')


if __name__ == '__main__':
    main()
