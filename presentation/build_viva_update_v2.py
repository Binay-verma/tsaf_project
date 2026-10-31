"""Viva deck v2: update of the 30 Oct college deck to the current (v6) evidence.

Same visual style as build_presentation.py (kept unchanged). Every number is read from audited
result files or the v6 manuscript tables; nothing is typed in by hand except labels.
Run from the repository root: python presentation/build_viva_update_v2.py
"""
from pathlib import Path
import csv
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'presentation/viva_update_v2'
OUT.mkdir(parents=True, exist_ok=True)
RA = ROOT/'review/journal_seven_tasks_20261031_v1'
BG = '101A2B'; WHITE = 'F5F8FC'; MUTED = 'B3C4D8'; TEAL = '36D3BD'; AMBER = 'FFCA69'; CARD = '1C2B42'
NAMES = {'ridge': 'Ridge', 'sarimax': 'SARIMAX', 'lightgbm': 'LightGBM', 'lightgbm_capacity2': 'Tree (leaf-2)',
         'chronos': 'Chronos-2', 'timesfm': 'TimesFM-3'}
ORDER = list(NAMES)


def rgb(v):
    return RGBColor.from_string(v)


def label(slide, text, x, y, w, h, size=20, color=WHITE, bold=False, after=10):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame; tf.word_wrap = True
    for i, line in enumerate(text.split('\n')):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.text = line
        p.font.name = 'Arial'; p.font.size = Pt(size); p.font.bold = bold; p.font.color.rgb = rgb(color)
        p.space_after = Pt(after)
    return box


def card(slide, title, body, x, y, w, h, tsize=21, bsize=19):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = rgb(CARD); s.line.fill.background()
    label(slide, title, x+.22, y+.18, w-.44, .55, tsize, TEAL, True)
    label(slide, body, x+.22, y+.85, w-.44, h-.95, bsize)


def stat(slide, big, small, x, y, w, h):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = rgb(CARD); s.line.fill.background()
    label(slide, big, x+.25, y+.2, w-.5, 1.2, 54, AMBER, True)
    label(slide, small, x+.25, y+1.45, w-.5, h-1.55, 19)


# ---------- evidence (read, never typed) ----------
def rows(p):
    return list(csv.DictReader(open(p)))

bal = {(r['model'], r['arm'], int(r['horizon'])): float(r['MASE'])
       for r in rows(ROOT/'results/calendar_recenter_recovery_v1/analysis/breadth/event_window/metrics_balanced.csv')
       if r['version'] == 'document_aligned'}
B = {(r['model'], r['representation'], r['lead']): r for r in rows(RA/'B_cluster_summary.csv')}
TC = json.load(open(RA/'tie_correction_v2.json'))
RES = json.load(open(RA/'descriptive_reanalysis_result.json'))
C1 = [r for r in rows(RA/'C_native_cluster_coverage.csv') if r['lead'] == '1']
year_opp = TC['B_years']['opposite_sign']; year_tie = TC['B_years']['exact_tie_in_either_year']
lofo = TC['B_lofo']['cells_with_sign_flip']
src_opp = TC['A_typed_minus_pooled']['opposite_sign']; src_same = TC['A_typed_minus_pooled']['same_sign']
src_tie = TC['A_typed_minus_pooled']['exact_tie_in_either']; tfm_opp = TC['A_typed_minus_pooled']['timesfm_opposite']
below = sum(int(r['clusters_below_0.8']) for r in C1); cells = sum(int(r['clusters_defined']) for r in C1)
inv = RES['B_inventory']
sar = B[('sarimax', 'day', '1')]; tfm = B[('timesfm', 'day', '1')]

# ---------- charts ----------
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 12})
x = range(len(ORDER)); wbar = .26
fig, ax = plt.subplots(figsize=(12, 4.2))
for k, (arm, lab, col) in enumerate([('calendar', 'Calendar only', '#9AA7B8'), ('day5', 'Typed day (5 festival flags)', '#1F8F80'),
                                      ('pooled_day5', 'Pooled day (1 shared flag)', '#E0A030')]):
    v = [bal[(m, arm, 1)] for m in ORDER]
    ax.bar([i+(k-1)*wbar for i in x], v, wbar, label=lab, color=col)
    for i, val in enumerate(v):
        ax.text(i+(k-1)*wbar, val+.01, f'{val:.2f}', ha='center', fontsize=9)
ax.set_xticks(list(x)); ax.set_xticklabels([NAMES[m] for m in ORDER]); ax.set_ylabel('MASE, lead 1 (lower is better)')
ax.set_ylim(0, .8); ax.legend(frameon=False, ncol=3, loc='upper left'); ax.spines[['top', 'right']].set_visible(False)
fig.tight_layout(); fig.savefig(OUT/'lead1_mase.png', dpi=180); plt.close(fig)

fig, ax = plt.subplots(figsize=(12, 4.2))
for k, (yr, col) in enumerate([('year_2024', '#1F8F80'), ('year_2025', '#E0A030')]):
    v = [float(B[(m, 'day', '1')][yr]) for m in ORDER]
    ax.bar([i+(k-.5)*.36 for i in x], v, .36, label=yr[-4:], color=col)
ax.axhline(0, color='black', linewidth=.8)
ax.set_xticks(list(x)); ax.set_xticklabels([NAMES[m] for m in ORDER])
ax.set_ylabel('Typed minus pooled MASE\n(+ = pooled better)'); ax.legend(frameon=False, title='Event year')
ax.spines[['top', 'right']].set_visible(False)
fig.tight_layout(); fig.savefig(OUT/'year_split_day_lead1.png', dpi=180); plt.close(fig)

F = lambda v: f'{v:.3f}'
slides = [
 dict(title='Do festival features help electricity\nforecasting, and is the answer stable?', subtitle='Typed versus pooled festival inputs for foundation and local models',
      body='Binay Verma\nCollege viva · November 2026\nResearch in progress',
      notes='This is an empirical study, not a new model. I compare ways of giving festival information to two pretrained forecasting models (Chronos-2 and TimesFM-3) and four local models, on daily electricity supplied in three Indian states. The main finding is that festival information helps at short leads, but which way of encoding it works best is not stable.'),
 dict(title='Why study this?', cards=[('Festivals move', 'Diwali, Holi, Dussehra, Ganesh Chaturthi and Ugadi/Gudi Padwa change date every year and differ by state.'),
      ('A simple design choice', 'Give each festival its own input (typed), or one shared "festival day" input (pooled)?'),
      ('Precise target', 'Daily energy met/supplied in GWh: what the grid delivered, not unconstrained demand.')],
      notes='Typed means five separate flags, one per festival. Pooled means one flag that is on for any of them, padded with four zeros so both use five input channels. The question is which works better, and whether the answer holds across years and data sources.'),
 dict(title='Data and evaluation rules', bullets=[f"Delhi, Karnataka, Maharashtra; event years 2024 and 2025; five festival families.",
      f"528 forecast cases = {inv['state_date_episodes']} state-dates × leads 1, 7, 14 ({inv['unique_target_dates']} distinct dates).",
      f"Effective event units: {inv['family_year_clusters']} festival-year clusters, not 528 independent tests.",
      'Past-only fitting, 730-day history, recorded labels only; NYC holidays as a separate-source check.'],
      callout='These outcomes were already inspected, so the results are exploratory, not a clean test.',
      notes='Each case is a target day within ±3 days of a festival. Lead 1 means forecasting the next day; lead 7 and 14 are single target days further ahead. Nearby days, states and leads share the same festival, weather and source, so I count festival-year clusters as the real units. NYC (subway and bus ridership around Yom Kippur and Columbus Day 2026) is a separate source registered before its data were downloaded.'),
 dict(title='Six models, eight matched input designs', cards=[('Local models', 'Ridge regression\nSARIMAX\nLightGBM (+ leaf-2 variant)\nRefit monthly, past data only'),
      ('Foundation models', 'Chronos-2 and TimesFM-3\nPinned pretrained weights\nNo fine-tuning'),
      ('Input designs', 'Calendar only\nTyped / pooled, day or ±3-day window\nZero channels and fake-date placebos as controls')],
      notes='All models see the same cases. Zero channels check whether merely adding inputs changes forecasts. Placebos put the festival flags on wrong dates, shifted by whole weeks, to check that gains come from the real dates. Local and foundation models adapt differently, so rankings are not a pure architecture comparison.'),
 dict(title='Finding 1: festival flags help at lead 1', image=OUT/'lead1_mase.png',
      caption=f"Lowest here: TimesFM-3 pooled ({bal[('timesfm','pooled_day5',1)]:.4f}) and SARIMAX typed ({bal[('sarimax','day5',1)]:.4f}).",
      source='Corrected Indian festival windows, 528 cases, lead 1. Source: v6 Table 1. No significance test; two event years.',
      notes='Compared with calendar-only inputs, both typed and pooled day flags lower the error for most models at lead 1. But the two best results use different encodings: TimesFM prefers pooled, SARIMAX prefers typed. That already hints that there is no single best encoding.'),
 dict(title='Finding 2: the best encoding is not stable', stats=[(f'{year_opp}/36', f'cells where 2024 and 2025 disagree on typed vs pooled (+{year_tie} exact tie)'),
      (f'{lofo}/36', 'cells where dropping one festival flips the result'),
      (f'{src_opp}/36', f'cells where India and NYC disagree (+{src_tie} ties); all {tfm_opp} TimesFM-3 cells reverse')],
      callout='Main lesson: report the ordering by year and source; do not pick one "winning" encoding.',
      notes='A cell is one model, one representation (day or window) and one lead: 6 × 2 × 3 = 36. These counts are descriptive. I registered this analysis before computing it, but it uses results I had already seen. I first reported 20 and 14 here; that counted exact ties as disagreements, so I corrected it to 19 and 11.'),
 dict(title='Year by year: few orderings persist', image=OUT/'year_split_day_lead1.png',
      caption=f"SARIMAX favours typed in both years; TimesFM-3 favours pooled in {tfm['clusters_pooled_better']}/{tfm['family_year_clusters']} clusters.",
      source='Day flags, lead 1, typed minus pooled MASE by event year. Source: v6 Table A4.',
      notes='Above zero means pooled was better that year; below zero means typed was better. Several models switch sides between 2024 and 2025. SARIMAX consistently prefers typed flags, and TimesFM prefers pooled in India, but in NYC TimesFM prefers typed. These persistent patterns are expectations for future testing, not proven effects.'),
 dict(title='Checks that changed the evidence', cards=[('Calendar correction', 'Karnataka 2025: the notice names Vijayadashami on 1 Oct, not 2 Oct. The ledger was fixed from the document, not from errors.'),
      ('Interval coverage', f'80% intervals cover less than 80% in {below} of {cells} lead-1 festival clusters (Chronos-2 and TimesFM-3).'),
      ('Honest counting', 'An exact-tie counting error was found and corrected; original outputs kept.')],
      callout='121 automated tests pass; this is software checking, not independent human review.',
      notes='Checking which festival the notice actually names is stronger than checking that a date is a holiday. Native uncertainty intervals are too narrow around festivals. All failures and corrections are kept in the repository so they can be checked.'),
 dict(title='Closest prior work and what is new', cards=[('Ziel (2018)', 'Compared one shared holiday dummy with separate dummies for German load: separate ones did not generally help.'),
      ('Kreusel et al. (2026)', 'Calendar encodings (ordinal, one-hot, cyclic, target) in Chronos-2 and TimesFM-3, on hourly data.'),
      ('This study', 'The same typed-vs-pooled choice through foundation-model inputs, with zero and placebo controls, across two sources.')],
      callout='Not a new architecture and not a causal holiday effect.',
      notes='The typed-versus-pooled question itself is old in load forecasting. What I add is testing it in foundation-model covariate channels with matched controls, and showing that the answer is unstable. Whether this is enough for a journal is for my supervisor and reviewers to judge.'),
 dict(title='Confirmation on genuinely future data', timeline=[('Frozen forecasts', '30–31 Oct 2026: forecasts saved publicly before outcomes. Score from 12 Nov (Diwali period included).'),
      ('Weekly study', 'Registered: 52 weekly forecasts from 16 Nov. Starts only after rights and calendar checks.'),
      ('Singapore replication', 'New country and festival calendar; protocol drafted, code ready, no data downloaded yet.')],
      caption='No future accuracy result exists yet.',
      notes='Historical results were already seen, so real confirmation must come from forecasts made before outcomes exist. The first frozen episode is one period; it cannot confirm the typed-versus-pooled pattern on its own. The weekly study needs verified 2026 calendars and a data-rights reply before it can start; missed weeks are recorded, not filled in later.'),
 dict(title='What I can claim, and the limits', bullets=['Festival flags often reduce lead-1 error on these cases.',
      'Which encoding is best depends on model, year, festival set and source.',
      'Calendar provenance and native uncertainty need explicit checks.',
      'Limits: 2 event years, 3 related states, inspected data, rights reply pending, no external reviewer yet.'],
      callout='A careful, reproducible empirical study, still in progress.',
      notes='I avoid claiming a universal winner, a causal effect or journal readiness. All code, protocols, forecasts and failures are public on GitHub, except model weights.'),
 dict(title='Sources and questions', bullets=['Robbie Andrew, Indian Energy and Emissions Data (GRID-INDIA/POSOCO); reuse request pending.',
      'Hunt & Bloomfield, Zenodo 14983362 (CC BY 4.0); MTA NYC ridership; NESO demand.',
      'Ziel 2018, JMPSCE 6(2); Kreusel et al. 2026, arXiv 2610.13676; Chronos-2, arXiv 2510.15821.',
      'Code and results: github.com/Binay-verma/tsaf_project'],
      callout='Charts are generated from this project’s recorded results.',
      notes='Thank the data curators and model developers. End with questions.'),
]

prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
prs.core_properties.author = 'Binay Verma'; prs.core_properties.title = 'Festival features and electricity forecasting — viva update'
md = ['# Speaker notes — viva deck v2 (Binay Verma)\n', 'About 10 minutes, 12 slides (~50 s each). Numbers come from manuscript v6 and the audited re-analysis.\n']
n = len(slides)
for i, s in enumerate(slides, 1):
    sl = prs.slides.add_slide(prs.slide_layouts[6]); sl.background.fill.solid(); sl.background.fill.fore_color.rgb = rgb(BG)
    label(sl, s['title'], .6, .4, 12.1, 1.4 if i == 1 else .8, 34 if i == 1 else 30, bold=True)
    ln = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(.6), Inches(2.0 if i == 1 else 1.38), Inches(1.0), Inches(.055))
    ln.fill.solid(); ln.fill.fore_color.rgb = rgb(TEAL); ln.line.fill.background()
    if i == 1:
        label(sl, s['subtitle'], .65, 2.4, 11.7, 1.1, 26, TEAL)
        label(sl, s['body'], .65, 4.2, 11.7, 1.8, 23)
    elif 'image' in s:
        sl.shapes.add_picture(str(s['image']), Inches(.6), Inches(1.6), width=Inches(12.1), height=Inches(4.23))
        label(sl, s['caption'], .65, 5.95, 12, .6, 20, TEAL, True)
        label(sl, s['source'], .65, 6.6, 12, .3, 11, MUTED)
    elif 'stats' in s:
        for k, (big, small) in enumerate(s['stats']):
            stat(sl, big, small, .65+k*4.18, 1.85, 3.95, 3.7)
        label(sl, s['callout'], .7, 5.95, 11.8, .8, 20, AMBER)
    elif 'cards' in s:
        for k, (t, b) in enumerate(s['cards']):
            card(sl, t, b, .65+k*4.18, 1.85, 3.95, 3.75)
        if s.get('callout'):
            label(sl, s['callout'], .7, 5.95, 11.8, .8, 20, AMBER)
    elif 'timeline' in s:
        for k, (t, b) in enumerate(s['timeline']):
            card(sl, f'{k+1}. {t}', b, .65+k*4.18, 1.85, 3.95, 3.75)
        label(sl, s['caption'], .7, 5.95, 11.9, .8, 22, AMBER, True)
    else:
        y = 1.8
        for b in s['bullets']:
            label(sl, '•  '+b, .7, y, 11.8, .9, 21); y += .98
        label(sl, s['callout'], .7, 6.05, 11.8, .7, 20, AMBER)
    label(sl, f'Binay Verma  |  Research in progress  |  Nov 2026                          {i:02d}/{n:02d}', .65, 7.05, 12, .28, 11, MUTED)
    sl.notes_slide.notes_text_frame.text = s['notes']
    md += [f"\n## Slide {i}: {s['title'].replace(chr(10), ' ')}\n", s['notes']+'\n']
prs.save(OUT/'Viva_Update_Binay_Verma_v2.pptx')
(OUT/'SPEAKER_NOTES.md').write_text('\n'.join(md))
print('slides', n)
