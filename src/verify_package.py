"""Verify the transferred checkpoint with Python's standard library only."""
from pathlib import Path
import hashlib
import json
import sys

def main():
 root=Path(__file__).resolve().parents[1]
 manifest=json.loads((root/'PACKAGE_CHECKSUMS.json').read_text())
 bad=[]
 for name,expected in manifest.items():
  path=root/name
  if not path.is_file():bad.append(f'Missing: {name}')
  elif hashlib.sha256(path.read_bytes()).hexdigest()!=expected:bad.append(f'Changed: {name}')
 if bad:
  print('\n'.join(bad));print('Investigate transfer corruption or intentional edits before claiming the checkpoint is unchanged.');return 1
 print(f'PASS: {len(manifest)} recorded checkpoint files match SHA-256 checksums. Scientific validity is not established by this check.')
 return 0
if __name__=='__main__':sys.exit(main())
