"""Restore fixed historical source snapshots; never fetch a live/latest series."""
from pathlib import Path
import gzip
import hashlib
import json
import urllib.request

ROOT=Path(__file__).resolve().parents[1]


def main():
    evidence=ROOT/'results/provenance_review_v1'
    cache=Path('/workspace/source-vintage-cache')
    cache.mkdir(exist_ok=True)
    git=json.loads((evidence/'git_vintage_audit.json').read_text())['snapshots']
    for snapshot in git:
        if not snapshot.get('commit'):continue
        path=cache/(snapshot['commit']+'.csv')
        if path.exists():raw=path.read_bytes()
        else:
            with urllib.request.urlopen(snapshot['source_url'],timeout=60) as f:raw=f.read()
        if hashlib.sha256(raw).hexdigest()!=snapshot['sha256']:
            raise ValueError('Git source byte hash mismatch; do not replace expected hash')
        path.write_bytes(raw)
        print('Verified recorded Git snapshot',snapshot['commit'][:12])
    archives=json.loads((evidence/'wayback_decoded_audit.json').read_text())['snapshots']
    for snapshot in archives:
        stamp=snapshot['capture_timestamp']
        path=cache/('wayback_'+stamp+'.csv')
        if path.exists():raw=path.read_bytes()
        else:
            url=f'https://web.archive.org/web/{stamp}id_/https://robbieandrew.github.io/india/data/POSOCO_data.csv'
            with urllib.request.urlopen(url,timeout=60) as f:raw=f.read()
        decoded=gzip.decompress(raw) if raw[:2]==b'\x1f\x8b' else raw
        # The decoded payload is the scientific artifact. Outer compression can vary.
        if hashlib.sha256(decoded).hexdigest()!=snapshot['decoded_sha256']:
            raise ValueError('Archived CSV payload hash mismatch; do not change expected hash')
        path.write_bytes(raw)
        (cache/('wayback_'+stamp+'_decoded.csv')).write_bytes(decoded)
        print('Verified recorded archive payload',stamp)


if __name__=='__main__':
    main()
