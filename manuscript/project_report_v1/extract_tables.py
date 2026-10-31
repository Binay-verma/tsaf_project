"""Extract audited tables from manuscript v6 into JSON for the project report (no retyping)."""
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
md = (ROOT/'manuscript/integrated_review_v6/MANUSCRIPT.md').read_text()
out = {}
for m in re.finditer(r'(?m)^(Table (?:A?\d+))\. (.*?)\n\n((?:\|.*\n)+)', md):
    rows = [[c.strip() for c in line.strip().strip('|').split('|')] for line in m.group(3).strip().split('\n')]
    rows = [r for r in rows if not all(set(c) <= set('-: ') for c in r)]
    out[m.group(1)] = dict(caption=m.group(2).strip(), header=rows[0], rows=rows[1:])
json.dump(out, open(Path(__file__).parent/'tables.json', 'w'), indent=1)
print({k: (len(v['rows']), len(v['header'])) for k, v in out.items()})
