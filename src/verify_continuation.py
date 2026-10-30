"""Verify the current continuation checkpoint without external dependencies."""
from pathlib import Path
import hashlib
import json
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root/'CONTINUATION_CHECKSUMS_20261030.json').read_text())
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
