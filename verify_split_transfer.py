"""Check either transfer part or the merged checkpoint; standard library only."""
from pathlib import Path
import argparse,hashlib,json,sys
p=argparse.ArgumentParser();p.add_argument('--part',choices=['core','data','all'],default='all');a=p.parse_args()
r=Path(__file__).resolve().parent;m=json.loads((r/'SPLIT_PACKAGE.json').read_text());names=['core','data'] if a.part=='all' else [a.part];bad=[];count=0
for part in names:
 for name,expected in m['parts'][part]['files'].items():
  count+=1;f=r/name
  if not f.is_file():bad.append('Missing: '+name)
  elif hashlib.sha256(f.read_bytes()).hexdigest()!=expected:bad.append('Changed: '+name)
if bad:
 print('\n'.join(bad));print('Extract the required archive(s) into the same parent, or investigate intentional edits.');sys.exit(1)
print(f'PASS: {count} original checkpoint entries verified for {a.part}. This checks transfer integrity, not scientific validity.')
