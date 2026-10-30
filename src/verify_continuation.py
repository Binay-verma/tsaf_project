"""Verify the current continuation checkpoint without external dependencies."""
from pathlib import Path
import argparse
import hashlib
import json
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path)
    args = parser.parse_args()
    default = ('GITHUB_CHECKSUMS_20261030.json' if
               (root/'GITHUB_CHECKSUMS_20261030.json').is_file()
               else 'CONTINUATION_CHECKSUMS_20261030.json')
    manifest = json.loads((args.manifest or root/default).read_text())
    bad = []
    for name, expected in manifest['files'].items():
        path = root/name
        if not path.is_file():
            bad.append('Missing: '+name)
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            bad.append('Changed: '+name)
    if bad:
        print('\n'.join(bad))
        return 1
    print(f"PASS: {len(manifest['files'])} continuation files verified; scientific validity is separate.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
