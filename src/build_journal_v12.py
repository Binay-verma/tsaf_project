"""Journal draft v12: v11 plus the second registered test, with companion tables moved to an online supplement.

Changes from v11 (manuscript/journal_v11/MANUSCRIPT.md), no v11 result number changed:
  * Appendix A (companion tables) and Appendix D (reproduction map) move to Supplement S1 and S2; Table A<n> -> Table S<n>.
  * The second registered test (results/new_states_v2/analysis) is added as Section 6.2, with matching sentences in the
    abstract, highlights, contributions, limitations and conclusion (second_test.py-style text built from the result files).
Run: python src/build_journal_v12.py   (refuses to overwrite manuscript/journal_v12)
"""
import datetime
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V11 = ROOT/'manuscript/journal_v11'
OUT = ROOT/'manuscript/journal_v12'
SECOND = ROOT/'results/new_states_v2/analysis'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def one(text, old, new):
    assert text.count(old) == 1, (text.count(old), old[:80])
    return text.replace(old, new)


src = (V11/'MANUSCRIPT.md').read_text()
text = one(src, '**Draft for supervisor review (journal format, version 11). Not submitted.**',
           '**Draft for supervisor review (journal format, version 12). Not submitted.**')

# ---------------- supplement split ----------------
head, rest = text.split('## Appendix A. Companion tables', 1)
app_a, rest = rest.split('## Appendix B. NYC transit replication', 1)
app_bc, app_d = rest.split('## Appendix D. Reproduction map', 1)
text = head + '## Appendix B. NYC transit replication' + app_bc
text = text.rstrip() + '\n'
supp = ('# Online supplement\n\nTyped or pooled festival indicators? Evidence from ten Indian states with registered tests\n\n'
        '## S1. Companion tables' + app_a.rstrip() + '\n\n## S2. Reproduction map' + app_d)
n_tables = len(re.findall(r'(?m)^Table A\d+\.', supp))
text = re.sub(r'\bTable(s?) A(\d+)', r'Table\1 S\2', text)
text = re.sub(r'(?<=, )A(\d+)\b', r'S\1', text)
text = re.sub(r'(?<= and )A(\d+)\b', r'S\1', text)
supp = re.sub(r'\bTable(s?) A(\d+)', r'Table\1 S\2', supp)
assert not re.search(r'\bTables? A\d', text) and not re.search(r'\bA\d+\b', re.sub(r'\[[^\]]*\]', '', text.split('## References')[0])), 'stray A-table reference'

# ---------------- second test ----------------
SECOND_TEXT = None
if (SECOND/'summary.json').exists():
    import second_test_text_v12 as st
    SECOND_TEXT = st.build(SECOND)
    for old, new in SECOND_TEXT['replacements']:
        text = one(text, old, new)

# ---------------- checks ----------------
heads = set(re.findall(r'(?m)^##+ ((?:Appendix )?[A-Z]?[0-9.]+[0-9A-Z]?)', text))
for m in re.finditer(r'\bSections? ((?:\d+(?:\.\d+)?)(?:(?:,\s*|\s+and\s+|\s+to\s+)\d+(?:\.\d+)?)*)', text.split('## References')[0]):
    for t in re.findall(r'\d+(?:\.\d+)?', m.group(1)):
        assert t in {h.rstrip('.') for h in heads} or t + '.' in heads, ('missing section', t)
capt = set(re.findall(r'(?m)^Table ([A-Z]?\d+b?)\.', text)) | set(re.findall(r'(?m)^Table (S\d+)\.', supp))
for m in re.finditer(r'\bTables? ((?:[A-Z]?\d+b?)(?:(?:,\s*|\s+and\s+|–)[A-Z]?\d+b?)*)', text + supp):
    for t in re.findall(r'[A-Z]?\d+b?', m.group(1)):
        assert t in capt, ('missing table', t)
cited = {int(x) for grp in re.findall(r'\[(\d+(?:,\s*\d+)*)\]', text.split('## References')[0]) for x in grp.split(',')}
listed = {int(x) for x in re.findall(r'(?m)^\[(\d+)\]', text.split('## References')[1])}
assert cited <= listed, cited - listed
abstract = text.split('## Abstract\n\n', 1)[1].split('\n\n', 1)[0]
assert 100 <= len(abstract.split()) <= 150, len(abstract.split())

# ---------------- output ----------------
OUT.mkdir(parents=True, exist_ok=False)
shutil.copytree(V11/'figures', OUT/'figures')
shutil.copytree(V11/'supplement', OUT/'supplement')
if SECOND_TEXT:
    for f in sorted(SECOND.glob('*.csv')):
        shutil.copy2(f, OUT/'supplement'/f'new_states_v2_{f.name}')
(OUT/'MANUSCRIPT.md').write_text(text)


def render(md, name):
    p = OUT/f'{name}.md'
    p.write_text(md)
    subprocess.run(['pandoc', str(p), '-o', str(OUT/f'{name}.docx'), '--resource-path', str(OUT)], check=True)
    subprocess.run(['soffice', '-env:UserInstallation=file:///tmp/tsfm-journal-v12-lo', '--headless', '--convert-to', 'pdf',
                    '--outdir', str(OUT), str(OUT/f'{name}.docx')], check=True, capture_output=True)
    p.unlink()


render(text, 'Typed_or_Pooled_Binay_Verma_v12')
blind = text.replace('Binay Verma\n\nAffiliation: __________ . Corresponding author email: __________ .\n\n', '')
blind = blind.replace('**Draft for supervisor review (journal format, version 12). Not submitted.**', '**Anonymised manuscript for review.**')
blind = blind.replace('https://github.com/Binay-verma/tsaf_project', '[repository link withheld for review]')
blind = re.sub(r'https://osf\.io/\w+', '[registration link withheld for review]', blind)
blind = re.sub(r'osf\.io/\w+', '[registration withheld for review]', blind)
blind = blind.replace('An earlier version of this study,', 'A preliminary analysis,').replace('the earlier version', 'a preliminary analysis')
blind = blind.split('**Funding.**')[0] + '**Funding, competing interests, author contributions, use of generative AI:** on the separate title page.\n\n## References' + blind.split('## References', 1)[1]
for ident in ['Binay', 'Verma', 'github.com/Binay', 'osf.io']:
    assert ident not in blind, ident
render(blind, 'Typed_or_Pooled_v12_anonymised')
sblind = supp.replace('https://github.com/Binay-verma/tsaf_project', '[repository link withheld for review]')
sblind = re.sub(r'https://osf\.io/\w+', '[registration link withheld for review]', sblind)
sblind = re.sub(r'osf\.io/\w+', '[registration withheld for review]', sblind)
for ident in ['Binay', 'Verma', 'github.com/Binay', 'osf.io']:
    assert ident not in sblind, ('supplement', ident)
render(sblind, 'Online_supplement_v12_anonymised')
render(supp, 'Online_supplement_v12')
json.dump(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               status='Journal-format draft v12; not submitted.',
               base={'manuscript/journal_v11/MANUSCRIPT.md': sha(V11/'MANUSCRIPT.md')},
               second_test={str(p.relative_to(ROOT)): sha(p) for p in sorted(SECOND.glob('*'))} if SECOND_TEXT else None,
               supplement_tables=n_tables, abstract_words=len(abstract.split()),
               words_main_text=len(text.split('## Declarations')[0].split()),
               outputs={p.name: sha(p) for p in sorted(OUT.glob('*')) if p.is_file()}), open(OUT/'build.json', 'w'), indent=1)
print('built; main words', len(text.split('## Declarations')[0].split()), 'supplement tables', n_tables, 'second test', bool(SECOND_TEXT))
