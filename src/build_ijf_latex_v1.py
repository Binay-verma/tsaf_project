"""IJF submission files in the Elsevier elsarticle template (author-year references), from journal v13.

Inputs: manuscript/journal_v13/MANUSCRIPT.md and SUPPLEMENT.md (built by src/build_journal_v13.py), the v13 figures,
and the elsarticle class (manuscript/ijf_template/elsarticle.cls, generated from the template the author supplied).
Outputs (manuscript/ijf_submission_v1/):
  manuscript_anonymised.tex/.pdf   double-anonymised main paper (review mode: double spacing), author-year references
  title_page.tex/.pdf              title, author, affiliation, declarations (not sent to reviewers)
  highlights.txt / highlights.docx
  figure1.pdf ... figure3.pdf      figures as separate files; figure_captions.txt
  supplementary_material.pdf       anonymised online supplement with author-year citations
Numbers are not retyped: the text, tables and captions come from v13; only the markup changes.
Run: python src/build_ijf_latex_v1.py
"""
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V13 = ROOT/'manuscript/journal_v13'
TPL = ROOT/'manuscript/ijf_template'
OUT = ROOT/'manuscript/ijf_submission_v1'

# ---------------- references: number -> (key, label authors, year) ----------------
LAB = {1: ('Ziel', '2018'), 2: ('Arora and Taylor', '2018'), 3: ('Ansari et~al.', '2025'), 4: ('Jain and Sen', '2026'),
       5: ('Kreusel et~al.', '2026'), 6: ('Alipour et~al.', '2025'), 7: ('Boylan et~al.', '2015'), 8: ('Hong and Fan', '2016'),
       9: ('Charlton and Singleton', '2014'), 10: ('Ziel and Liu', '2016'), 11: ('Arora and Taylor', '2013'), 12: ('Banerjee and Sarkar', '2010'),
       13: ('Fernandes et~al.', '2011'), 14: ('Sanyal et~al.', '2017'), 15: ('Liu', '1980'), 16: ('Bell and Hillmer', '1983'),
       17: ('Findley et~al.', '1998'), 18: ('Lin and Liu', '2003'), 19: ('Roberts and White', '2015'), 20: ('Taylor and Letham', '2018'),
       21: ('Probst et~al.', '2019'), 22: ('{LightGBM developers}', '2026'), 23: ('Das et~al.', '2024'), 24: ('Ansari et~al.', '2024'),
       25: ('Woo et~al.', '2024'), 26: ('Ekambaram et~al.', '2024'), 27: ('Pineda~Arango et~al.', '2025'), 28: ('Kaljevic et~al.', '2026'),
       29: ('Meyer et~al.', '2025'), 30: ('Hyndman and Koehler', '2006'), 31: ('Franses', '2016'), 32: ('Canay et~al.', '2017'),
       33: ('Hemerik et~al.', '2020'), 34: ('Diebold and Mariano', '1995'), 35: ('Holm', '1979'), 36: ('Nosek et~al.', '2018'),
       37: ('Bates and Granger', '1969'), 38: ('Claeskens et~al.', '2016'), 39: ('Ke et~al.', '2017'), 40: ('Romano et~al.', '2019')}


def key(n):
    a, y = LAB[n]
    return re.sub(r'[^a-z]', '', a.split()[0].lower()) + y + ('b' if n in (3, 2) else '')


def plain(n):
    return LAB[n][0].replace('~', ' ').replace('{', '').replace('}', '') + ', ' + LAB[n][1]


def refs(md):
    return {int(n): t for n, t in re.findall(r'(?m)^\[(\d+)\] (.+)$', md)}


def tex_escape(s):
    s = s.replace('\\', r'\textbackslash{}')
    for a, b in [('&', r'\&'), ('%', r'\%'), ('#', r'\#'), ('_', r'\_'), ('$', r'\$')]:
        s = s.replace(a, b)
    return s


def ref_entry(n, text):
    urls = re.findall(r'https?://\S+', text)
    body = text if n != 22 else text.replace('LightGBM developers. ', 'LightGBM developers (2026). ')
    for u in urls:
        body = body.replace(u, '\x00%d\x00' % urls.index(u))
    body = tex_escape(body)
    for i, u in enumerate(urls):
        body = body.replace('\x00%d\x00' % i, r'\url{' + u.rstrip('.') + '}')
    a, y = LAB[n]
    return f'\\bibitem[{{{a}({y})}}]{{{key(n)}}}\n{body}\n'


# ---------------- markdown -> LaTeX ----------------
def cites_to_tokens(md):
    # "Ziel [1] compared" -> \citet; other [n, m] -> \citep
    def repl(m):
        nums = [int(x) for x in m.group(2).split(',')]
        pre = m.group(1)
        if len(nums) == 1:
            name = LAB[nums[0]][0].replace('~', ' ').replace('{', '').replace('}', '')
            if pre.rstrip().endswith(name):
                return pre.rstrip()[:-len(name)] + f'ZZCITET{key(nums[0])}ZZ'
        return pre + 'ZZCITEP' + ','.join(key(n) for n in nums) + 'ZZ'
    return re.sub(r'((?:[A-Z][\w\-]*(?: et al\.| and [A-Z][\w\-]*)? )?)\[(\d+(?:,\s*\d+)*)\]', repl, md)


def round3(cell):
    def r(m):
        v = float(m.group(2))
        return m.group(1)+(f'{v:.3f}' if abs(v) >= 0.1 else m.group(2))
    # unsigned levels (MASE values) only; signed differences keep their digits
    return re.sub(r'(^|[\s(])(\d\.\d{4,})', r, cell)


def md_table(lines, caption, n):
    rows = [[c.strip() for c in l.strip().strip('|').split('|')] for l in lines if not re.match(r'^\|\s*-', l)]
    head, body = rows[0], rows[1:]
    cols = len(head)
    def cell(c):
        c = tex_escape(round3(c))
        c = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', c)
        return c
    wide = [max(len(r[i]) for r in rows) > 9 for i in range(cols)]
    spec = ''.join('>{\\raggedright\\arraybackslash}X' if w else 'l' for w in wide)
    env = 'tabularx' if any(wide) else 'tabular'
    width = '{\\textwidth}' if any(wide) else ''
    out = ['\\begin{table}[htbp]', '\\centering', '\\def\\baselinestretch{1}\\footnotesize', f'\\caption{{{cap_tex(caption)}}}', f'\\label{{tab:{n}}}',
           f'\\begin{{{env}}}{width}{{{spec}}}', '\\toprule', ' & '.join(cell(c) for c in head) + ' \\\\', '\\midrule']
    out += [' & '.join(cell(c) for c in r) + ' \\\\' for r in body]
    out += ['\\bottomrule', f'\\end{{{env}}}', '\\end{table}']
    return '\n'.join(out)


def cap_tex(c):
    c = tex_escape(c)
    c = re.sub(r'ZZCITE([PT])([a-z0-9,]+)ZZ', lambda m: ('\\citep{' if m.group(1) == 'P' else '\\citet{') + m.group(2) + '}', c)
    return c


def convert(md):
    """Body markdown (from Introduction to before Declarations) -> LaTeX."""
    md = cites_to_tokens(md)
    blocks, out_md = {}, []
    lines = md.split('\n'); i = 0; tcount = 0; fcount = 0
    while i < len(lines):
        l = lines[i]
        m = re.match(r'^Table (\d+)\. (.+)$', l)
        if m:
            j = i+1
            while j < len(lines) and not lines[j].startswith('|'):
                j += 1
            k = j
            while k < len(lines) and lines[k].startswith('|'):
                k += 1
            tcount += 1; assert int(m.group(1)) == tcount, (m.group(1), tcount)
            tok = f'ZZBLOCK{len(blocks)}ZZ'; blocks[tok] = md_table(lines[j:k], m.group(2), m.group(1))
            out_md.append(tok); i = k; continue
        m = re.match(r'^!\[Figure (\d)\. (.+)\]\(figures/(.+?)\.png\)$', l)
        if m:
            fcount += 1; assert int(m.group(1)) == fcount
            tok = f'ZZBLOCK{len(blocks)}ZZ'
            blocks[tok] = ('\\begin{figure}[htbp]\n\\centering\n' + f'\\includegraphics[width=\\textwidth]{{figure{m.group(1)}.pdf}}\n'
                           + f'\\caption{{{cap_tex(m.group(2))}}}\n\\label{{fig:{m.group(1)}}}\n\\end{{figure}}')
            out_md.append(tok); i += 1; continue
        out_md.append(l); i += 1
    body = '\n'.join(out_md)
    body = re.sub(r'(?m)^(#{2,3}) \d+(?:\.\d+)?\.? ', r'\1 ', body)
    tex = subprocess.run(['pandoc', '-f', 'markdown-auto_identifiers', '-t', 'latex', '--wrap=preserve'], input=body, capture_output=True, text=True, check=True).stdout
    tex = tex.replace('\\section{', '\\section{').replace('\\subsection{', '\\subsection{')
    tex = re.sub(r'\\section\{', r'\\section{', tex)
    tex = re.sub(r'ZZCITE([PT])([a-z0-9,]+)ZZ', lambda m: ('\\citep{' if m.group(1) == 'P' else '\\citet{') + m.group(2) + '}', tex)
    for tok, b in blocks.items():
        assert tex.count(tok) == 1, tok
        tex = tex.replace(tok, b)
    # pandoc maps ## to \subsection; promote one level (## = section, ### = subsection)
    tex = tex.replace('\\subsection{', '\\SECTION{').replace('\\subsubsection{', '\\subsection{').replace('\\SECTION{', '\\section{')
    tex = re.sub(r'\\label\{[^}]*\}\n?', lambda m: m.group(0) if m.group(0).startswith('\\label{tab:') or m.group(0).startswith('\\label{fig:') else '', tex)
    tex = tex.replace('\\tightlist\n', '')
    return tex


PREAMBLE = r"""\documentclass[review,12pt,authoryear]{elsarticle}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{newunicodechar}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{array}
\usepackage{url}
\usepackage{lineno}
\newunicodechar{−}{\ensuremath{-}}
\newunicodechar{±}{\ensuremath{\pm}}
\newunicodechar{≥}{\ensuremath{\geq}}
\newunicodechar{≤}{\ensuremath{\leq}}
\newunicodechar{ρ}{\ensuremath{\rho}}
\newunicodechar{×}{\ensuremath{\times}}
\newunicodechar{’}{'}
\newunicodechar{‘}{`}
\newunicodechar{ü}{\"u}
\newunicodechar{ä}{\"a}
\newunicodechar{é}{\'e}
\newunicodechar{è}{\`e}
\providecommand{\tightlist}{}
\journal{International Journal of Forecasting}
"""


def blind(t):
    t = t.replace('https://github.com/Binay-verma/tsaf_project', '[repository link withheld for review]')
    t = re.sub(r'registered \(osf\.io/\w+\)', 'registered (OSF)', t)
    t = re.sub(r'https://osf\.io/\w+', '[registration link withheld for review]', t)
    t = re.sub(r'osf\.io/\w+', 'registration withheld for review', t)
    for ident in ['Binay', 'Verma', 'github.com/Binay', 'osf.io']:
        assert ident not in t, ident
    return t


AI_DECL = ('During the preparation of this work the author used Claude (Anthropic), an AI assistant, in order to write and run analysis code, '
           'search for and check calendar sources, draft and revise the text, and review the manuscript. After using this tool, the author '
           'reviewed and edited the content as needed and takes full responsibility for the content of the published article.')


def build_main(md):
    title = md.split('\n', 1)[0].lstrip('# ').strip()
    abstract = md.split('## Abstract\n\n', 1)[1].split('\n\n', 1)[0]
    kw = md.split('**Keywords:**', 1)[1].split('\n', 1)[0].strip().rstrip('.')
    highlights = re.findall(r'(?m)^- (.+)$', md.split('## Highlights', 1)[1].split('## 1.', 1)[0])
    body = '## 1.' + md.split('## 1.', 1)[1].split('## Declarations', 1)[0]
    decl = md.split('## Declarations', 1)[1].split('## References', 1)[0]
    data = decl.split('**Data availability.**', 1)[1].split('\n\n', 1)[0].strip()
    rmap = refs(md.split('## References', 1)[1])
    tex = convert(blind(body))
    words = [w for w in kw.split(';')]
    title_words = set(re.findall(r'[a-z]+', title.lower()))
    kws = [w.strip() for w in words if not (set(re.findall(r'[a-z]+', w.lower())) & title_words - {'of', 'and', 'the'})]
    bib = ''.join(ref_entry(n, rmap[n]) for n in sorted(rmap, key=lambda n: (LAB[n][0].replace('{', '').lower(), LAB[n][1])))
    doc = (PREAMBLE + '\\begin{document}\n\\begin{frontmatter}\n'
           + f'\\title{{{tex_escape(title)}}}\n'
           + f'\\begin{{abstract}}\n{tex_escape(abstract)}\n\\end{{abstract}}\n'
           + '\\begin{keyword}\n' + ' \\sep '.join(tex_escape(k) for k in kws) + '\n\\end{keyword}\n\\end{frontmatter}\n\\linenumbers\n'
           + tex
           + '\n\\section*{Data availability}\n' + convert(blind(data)).strip() + '\n'
           + '\n\\section*{Declaration of generative AI and AI-assisted technologies in the manuscript preparation process}\n' + AI_DECL + '\n'
           + '\n\\begingroup\\raggedright\n\\begin{thebibliography}{99}\n' + bib + '\\end{thebibliography}\n\\endgroup\n\\end{document}\n')
    return doc, title, highlights, kws, abstract


def title_page(title):
    return (PREAMBLE.replace('review,12pt', 'preprint,12pt') + '\\begin{document}\n\\begin{frontmatter}\n'
            + f'\\title{{{tex_escape(title)}}}\n'
            + '\\author{Binay Verma\\corref{cor1}}\n\\ead{[e-mail address]}\n\\cortext[cor1]{Corresponding author. Postal address: [full postal address].}\n'
            + '\\affiliation{organization={[Department, University]}, city={[City]}, country={India}}\n\\end{frontmatter}\n'
            + '\\section*{Declaration of competing interest}\n[The author declares that he has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.] Use the journal\'s declaration tool and upload its file as well.\n'
            + '\\section*{Funding}\n[This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.]\n'
            + '\\section*{CRediT authorship contribution statement}\n\\textbf{Binay Verma:} [Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Writing -- original draft, Writing -- review \\& editing, Visualization].\n'
            + '\\section*{Declaration of generative AI and AI-assisted technologies in the manuscript preparation process}\n' + AI_DECL + '\n'
            + '\\section*{Acknowledgements}\n[None, or names of people who helped, with their agreement.]\n'
            + '\\section*{Data and registrations}\nCode, protocols, forecasts and audits: \\url{https://github.com/Binay-verma/tsaf_project}. Registrations: \\url{https://osf.io/yw7mr}, \\url{https://osf.io/f9tv4}, \\url{https://osf.io/xr25s}.\n'
            + '\\end{document}\n')


def latex(name):
    for _ in range(3):
        r = subprocess.run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', name+'.tex'], cwd=OUT, capture_output=True, text=True)
        if r.returncode:
            print(r.stdout[-3000:]); raise SystemExit(f'pdflatex failed: {name}')
    log = (OUT/(name+'.log')).read_text(errors='ignore')
    bad = re.findall(r'(Citation `[^\']+\' undefined|Reference `[^\']+\' undefined|Missing character[^\n]*)', log)
    assert not bad, bad[:10]


def supplement(md, main_md):
    rmap = refs(main_md.split('## References', 1)[1]) | refs(md.split('## References cited in the supplement', 1)[1])
    body = md.split('## References cited in the supplement', 1)[0]
    cited = sorted({int(x) for g in re.findall(r'\[(\d+(?:,\s*\d+)*)\]', body) for x in g.split(',')})
    body = re.sub(r'\[(\d+(?:,\s*\d+)*)\]', lambda m: '(' + '; '.join(plain(int(x)) for x in m.group(1).split(',')) + ')', body)
    lst = sorted(cited, key=lambda n: (LAB[n][0].replace('{', '').lower(), LAB[n][1]))
    body += '\n## References cited in the supplement\n\n' + '\n\n'.join(rmap[n] for n in lst) + '\n'
    return blind(body)


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    shutil.copy2(TPL/'elsarticle.cls', OUT/'elsarticle.cls')
    md = (V13/'MANUSCRIPT.md').read_text()
    doc, title, hl, kws, abstract = build_main(md)
    assert 100 <= len(abstract.split()) <= 150 and len(kws) >= 5, (len(abstract.split()), kws)
    assert all(len(h) <= 85 for h in hl) and 3 <= len(hl) <= 5
    for i in (1, 2, 3):
        shutil.copy2(V13/'figures'/f'figure{i}.pdf', OUT/f'figure{i}.pdf')
    (OUT/'manuscript_anonymised.tex').write_text(doc)
    (OUT/'title_page.tex').write_text(title_page(title))
    latex('manuscript_anonymised'); latex('title_page')
    (OUT/'highlights.txt').write_text('\n'.join(hl) + '\n')
    subprocess.run(['pandoc', '-o', str(OUT/'highlights.docx')], input='# Highlights\n\n' + '\n'.join('- '+h for h in hl), text=True, check=True)
    caps = re.findall(r'!\[(Figure \d\. .+?)\]\(', md)
    (OUT/'figure_captions.txt').write_text('\n\n'.join(caps) + '\n')
    s = supplement((V13/'SUPPLEMENT.md').read_text(), md)
    (OUT/'supplementary_material.md').write_text(s)
    subprocess.run(['pandoc', 'supplementary_material.md', '-o', 'supplementary_material.docx', '--resource-path', str(V13)], cwd=OUT, check=True)
    subprocess.run(['soffice', '-env:UserInstallation=file:///tmp/tsfm-ijf-lo', '--headless', '--convert-to', 'pdf', 'supplementary_material.docx'], cwd=OUT, check=True, capture_output=True)
    for f in OUT.glob('*'):
        if f.suffix in ('.aux', '.log', '.out', '.spl') or f.name == 'elsarticle.cls':
            f.unlink()
    print('built', sorted(p.name for p in OUT.iterdir()), 'keywords', kws)


if __name__ == '__main__':
    main()
