"""Build integrated review v7 from the unchanged v6 manuscript.

Adds the registered Ziel (2018) comparators (hSun, Rph, RpH) for the local models on
India and NYC, the Singapore metadata-check outcome and a corrected description of
Ziel's findings. Exact, asserted text insertions; every new number is computed here
from committed analysis files. v6 is never modified.
Run from the repository root: python src/build_integrated_review_v7.py
"""
import csv, datetime, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V6 = ROOT / "manuscript/integrated_review_v6"
OUT = ROOT / "manuscript/integrated_review_v7"
I1 = ROOT / "results/ziel_replacing_v1/analysis"
I2 = ROOT / "results/ziel_replacing_v2/analysis"
NY = ROOT / "results/ziel_nyc_v1/analysis"
SG = ROOT / "review/singapore_c3_metadata_check_v1/record.json"
NAMES = {"ridge": "Rich Ridge", "sarimax": "SARIMAX", "lightgbm": "Stable LightGBM", "lightgbm_capacity2": "Tree leaf minimum 2"}
LOCAL = ["ridge", "sarimax", "lightgbm", "lightgbm_capacity2"]
ARMS = [("calendar", "Calendar"), ("day5", "Typed day"), ("pooled_day5", "Pooled day"),
        ("sunday_day", "hSun"), ("replace_pooled", "Rph"), ("replace_typed", "RpH")]
SHORT = {"sunday_day": "hSun", "replace_pooled": "Rph", "replace_typed": "RpH", "pooled_day5": "pooled day",
         "day5": "typed day", "calendar": "calendar"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return list(csv.DictReader(open(p)))


def f5(x):
    return f"{float(x):.5f}"


# ---------- checks must have passed ----------
for d in (I1, I2, NY):
    for cohort, c in json.load(open(d / "checks.json")).items():
        assert c["reference_predictions_match"] and c["stored_balanced_MASE_max_abs_diff"] < 1e-12, (d, cohort)
ref_diff = max(max(c.get("reference_max_abs_diff_GWh", 0) for c in json.load(open(d / "checks.json")).values()) for d in (I1, I2))
nyc_diff = max(c["reference_max_abs_diff"] for c in json.load(open(NY / "checks.json")).values())

# ---------- balanced MASE ----------
ib = {}
for d in (I1, I2):
    for r in read(d / "event_window_balanced.csv"):
        key = (r["model"], r["arm"], int(r["horizon"]))
        if key in ib:
            assert abs(ib[key] - float(r["MASE"])) < 1e-12  # reference arms agree across both runs
        ib[key] = float(r["MASE"])
nb = {(r["model"], r["arm"], int(r["horizon"])): float(r["MASE"]) for r in read(NY / "event_window_balanced.csv")}

# v6 Table 1 reference values must equal the recomputed reference arms
v6 = (V6 / "MANUSCRIPT.md").read_text()
for m in LOCAL:
    row = next(l for l in v6.splitlines() if l.startswith(f"| {NAMES[m]} |"))
    cells = [c.strip() for c in row.strip("|").split("|")]
    for (arm, _), cell in zip(ARMS[:3], cells[1:4]):
        assert f5(ib[(m, arm, 1)]) == cell, (m, arm, cell)

# ---------- contrasts ----------
IC = read(I1 / "event_window_contrasts.csv") + read(I2 / "event_window_contrasts.csv")
NC = read(NY / "event_window_contrasts.csv")


def cnt(rows, contrast, sign):
    v = [float(r["balanced"]) for r in rows if r["contrast"] == contrast]
    assert len(v) == 12, (contrast, len(v))
    return sum((x < 0) if sign < 0 else (x > 0) for x in v)


def lab(rows, contrast, label):
    return sum(r["label"] == label for r in rows if r["contrast"] == contrast)


i_hsun_cal = cnt(IC, "sunday_day - calendar", -1)
i_rph_cal = cnt(IC, "replace_pooled - calendar", -1)
i_rpH_cal = cnt(IC, "replace_typed - calendar", -1)
assert i_hsun_cal == i_rph_cal == i_rpH_cal == 12
i_rph_add = cnt(IC, "replace_pooled - pooled_day5", -1)
i_rpH_add = cnt(IC, "replace_typed - day5", -1)
i_rph_add_c = lab(IC, "replace_pooled - pooled_day5", "consistent")
i_rpH_add_c = lab(IC, "replace_typed - day5", "consistent")
n_hsun_cal = cnt(NC, "sunday_day - calendar", +1)
n_rph_cal = cnt(NC, "replace_pooled - calendar", +1)
n_rpH_cal = cnt(NC, "replace_typed - calendar", +1)
n_rph_add = cnt(NC, "replace_pooled - pooled_day5", -1)
n_rpH_add = cnt(NC, "replace_typed - day5", +1)
lgb = next(r for r in IC if r["model"] == "lightgbm" and r["contrast"] == "sunday_day - pooled_day5" and r["horizon"] == "1")
assert lgb["label"] == "consistent" and float(lgb["balanced"]) < 0
i_hsun_pool_neg = lab(IC, "sunday_day - pooled_day5", "negligible")

# typed-versus-pooled sign under replacing compared with the additive flags
add_i = {(m, h): ib[(m, "day5", h)] - ib[(m, "pooled_day5", h)] for m in LOCAL for h in (1, 7, 14)}
rep_i = {(m, h): ib[(m, "replace_typed", h)] - ib[(m, "replace_pooled", h)] for m in LOCAL for h in (1, 7, 14)}
same_i = sum(add_i[k] * rep_i[k] > 0 for k in add_i)
opp_i = [k for k in add_i if add_i[k] * rep_i[k] < 0]
assert same_i + len(opp_i) == 12 and opp_i == [("sarimax", 7)]
opp_i_add = add_i[("sarimax", 7)]
assert 0 < opp_i_add < 1e-5
add_n = {(m, h): nb[(m, "day5", h)] - nb[(m, "pooled_day5", h)] for m in LOCAL for h in (8, 14, 21)}
rep_n = {(m, h): nb[(m, "replace_typed", h)] - nb[(m, "replace_pooled", h)] for m in LOCAL for h in (8, 14, 21)}
same_n = sum(add_n[k] * rep_n[k] > 0 for k in add_n)
opp_n = sum(add_n[k] * rep_n[k] < 0 for k in add_n)
tie_n = 12 - same_n - opp_n
lgb_nyc_ties = [k for k in add_n if add_n[k] == 0 or rep_n[k] == 0]
assert all(k[0] == "lightgbm" for k in lgb_nyc_ties)
# India versus NYC under replacing
cross_same = sum(rep_i[(m, h)] * rep_n[(m, h + 7)] > 0 for m in LOCAL for h in (1, 7, 14))
cross_opp = sum(rep_i[(m, h)] * rep_n[(m, h + 7)] < 0 for m in LOCAL for h in (1, 7, 14))
cross_tie = 12 - cross_same - cross_opp

# consistency labels, the additive flags versus calendar, ordinary cohorts, year spread of negligible cells
def lab_up(rows, contrast):  # consistent cells whose balanced value is positive (a consistent rise)
    return sum(r["label"] == "consistent" and float(r["balanced"]) > 0 for r in rows if r["contrast"] == contrast)
n_hsun_cal_c = lab_up(NC, "sunday_day - calendar")
n_rph_cal_c = lab_up(NC, "replace_pooled - calendar")
n_rpH_cal_c = lab_up(NC, "replace_typed - calendar")
assert n_hsun_cal_c == lab(NC, "sunday_day - calendar", "consistent")
i_rpH_cal_c = lab(IC, "replace_typed - calendar", "consistent")
assert lab(IC, "sunday_day - calendar", "consistent") == 12 and lab(IC, "replace_pooled - calendar", "consistent") == 12
add_beats_cal = sum(ib[(m, a, h)] < ib[(m, "calendar", h)] for m in LOCAL for a in ("day5", "pooled_day5") for h in (1, 7, 14))
IO = read(I1 / "ordinary_contrasts.csv") + read(I2 / "ordinary_contrasts.csv")
NO = read(NY / "ordinary_contrasts.csv")
io_counts = [cnt(IO, f"{a} - calendar", -1) for a in ("sunday_day", "replace_pooled", "replace_typed")]
no_counts = [cnt(NO, f"{a} - calendar", -1) for a in ("sunday_day", "replace_pooled", "replace_typed")]
neg_rows = [r for r in IC if r["contrast"] == "sunday_day - pooled_day5" and r["label"] == "negligible"]
neg_year_max = max(max(abs(float(r["year_2024"])), abs(float(r["year_2025"]))) for r in neg_rows)
reg_times = {c: subprocess.run(["git", "log", "-1", "--format=%ad", "--date=format-local:%H:%M:%S", c], cwd=ROOT,
                               capture_output=True, text=True, env={"TZ": "UTC"}, check=True).stdout.strip() for c in ["86406ec"]}
first_analysis = json.load(open(I1 / "summary.json"))["created_utc"][11:19]
assert reg_times["86406ec"] < first_analysis

sg = json.load(open(SG))
assert sg["decision"].startswith("C3 NOT PASSED")

# ---------- edits ----------
E = [
 ("status",
  "**Integrated research draft for professor review, version 6. Not submitted or submission-ready.** Version 6 applies the internal claim-ledger revisions of 31 October 2026 to version 5; all version 5 result tables are unchanged.",
  "**Integrated research draft for professor review, version 7. Not submitted or submission-ready.** Version 7 adds registered daily adaptations of Ziel's holiday-as-Sunday and replacing designs for the local models (Sections 3–5, Tables A6–A9) and the Singapore metadata-check outcome to version 6; all version 6 tables are unchanged."),
 ("abstract",
  "Source revisions, sparse event years, unmatched adaptation policies,",
  f"Registered adaptations of Ziel's holiday-as-Sunday (hSun) and replacing (Rph, RpH) dummy designs lower local-model event MASE relative to calendar in all 12 Indian local model/lead cells for each design, as the additive flags also do, "
  f"but they differ consistently from the additive flags they carry in only {i_rph_add_c} (Rph) and {i_rpH_add_c} (RpH) of 12 cells, and in NYC hSun raises event MASE relative to calendar in {n_hsun_cal} of 12 cells ({n_hsun_cal_c} of them consistent). "
  "Source revisions, sparse event years, unmatched adaptation policies,"),
 ("closest work, Ziel findings",
  "and found that separate dummies did not generally improve on a single dummy, with univariate results mixed by holiday type.",
  "and reported that many additional per-holiday dummies did not seem to improve on one additional dummy, with univariate results mixed by holiday type; "
  "in his multivariate comparison three models were not significantly worse than the best model forecast, M-RpH (a replacing design with one dummy per holiday), and the holiday-as-Saturday and holiday-as-Sunday designs were in most cases significantly worse than the best approach."),
 ("closest work, new comparator",
  "What is examined here is how that choice behaves through foundation-model covariate channels under a fixed channel budget with zero and placebo controls.",
  "What is examined here is how that choice behaves through foundation-model covariate channels under a fixed channel budget with zero and placebo controls. "
  "Daily adaptations of Ziel's holiday-as-Sunday and replacing designs are also run for the local models (Sections 3–5)."),
 ("models, Ziel arms",
  "Equal dimensions do not imply equal information, and zero padding is not assumed inert.",
  "Equal dimensions do not imply equal information, and zero padding is not assumed inert.\n\n"
  "Three further local-model arms adapt Ziel's German load designs [9] to daily festival anchors. hSun treats every family anchor day as a Sunday (weekday one-hot replaced by the Sunday one-hot) with no festival indicator, plus five zeros. "
  "Rph adds the pooled day flag and sets all seven weekday dummies to zero on flagged days; RpH does the same with the five typed day flags (Ziel's Eq. 11). Each has 18 channels. "
  "Their protocols and analysis code were committed before any of their forecasts existed (commits a8975c9, 5e1e4dc and add10e1). These were local commits, not yet pushed when this draft was built, so the order rests on the author's commit history and file time stamps rather than a public timestamp. "
  "The cases' other arms had already been inspected, so the comparators are exploratory. "
  f"The hSun protocol first called that arm the replacing variant; a correction note was committed (86406ec, {reg_times['86406ec']} UTC) before its registered analysis ran ({first_analysis} UTC). "
  "Only the five festival families are treated, not all public holidays as in Ziel, and the lag features and SARIMAX's weekly seasonal term are not holiday-adjusted, so only the calendar channels change. "
  f"The same runs recompute the calendar, typed-day and pooled-day arms: they reproduce the stored forecasts within {ref_diff:.2e} GWh in India and exactly in NYC, and the stored balanced MASE within 1e-12. "
  "Foundation-model versions of these designs were not run."),
 ("India Ziel results",
  "Learned category means are past-only summaries of this dataset, not newly discovered holidays or learned causal event effects.",
  "Learned category means are past-only summaries of this dataset, not newly discovered holidays or learned causal event effects.\n\n"
  "Tables A6–A7 give the Ziel adaptations for the four local models. In India each design lowers event MASE relative to calendar in all 12 local model/lead cells "
  f"(consistent in 12, 12 and {i_rpH_cal_c} cells for hSun, Rph and RpH). The additive typed and pooled day flags also beat calendar in {add_beats_cal} of their 24 cells, so this gain is not specific to Ziel's designs. "
  f"Relative to the additive flags it carries, Rph is lower than pooled day in {i_rph_add} of 12 cells and RpH lower than typed day in {i_rpH_add} of 12, but the difference keeps its sign in both years and under every leave-one-family-out subset in only {i_rph_add_c} and {i_rpH_add_c} cells. "
  f"The balanced hSun-minus-pooled-day difference is below 0.005 MASE in {i_hsun_pool_neg} of 12 cells, although single years in those cells differ by up to {neg_year_max:.3f}; "
  f"the clear exception is Stable LightGBM, whose lead-1 hSun MASE is {f5(-float(lgb['balanced']))} below pooled day in both years and every leave-one-family-out subset. "
  f"On the Indian ordinary sample the three designs also lower MASE relative to calendar in {io_counts[0]}, {io_counts[1]} and {io_counts[2]} of 12 cells, so their effect is not confined to festival windows. "
  f"Replacing rarely reverses the local typed-versus-pooled ordering: RpH minus Rph has the same sign as typed minus pooled day in {same_i} of 12 cells; "
  f"the exception is SARIMAX at lead 7, where the additive difference is only {opp_i_add:.6f}."),
 ("NYC Ziel results",
  "Within NYC, 36 of 144 family/mode/step cells favour pooling, 96 favour separate identities and 12 tie.",
  "Within NYC, 36 of 144 family/mode/step cells favour pooling, 96 favour separate identities and 12 tie.\n\n__NYC_PLACEHOLDER__"),
 ("limits, generalisation",
  "India has two main event years; NYC contributes two occurrences from one city; NESO contributes no holiday targets.",
  "India has two main event years; NYC contributes two occurrences from one city; NESO contributes no holiday targets. "
  "A drafted Singapore replication was not registered because its metadata check did not pass: the EMA history start and whether the series is covered by the Singapore Open Data Licence could not be verified, and no demand data were acquired."),
 ("limits, closest methods",
  "Generic encodings, sparse pooling and pooled-versus-separate holiday dummies [9] have close prior work;",
  "Generic encodings, sparse pooling and pooled-versus-separate holiday dummies [9] have close prior work; Ziel's holiday-as-Sunday and replacing designs are now compared for the local models only; their advantage over calendar in Indian festival windows, which the additive flags share, does not carry over to NYC event windows;"),
]

nyc_par = (f"Tables A8–A9 repeat the Ziel adaptations on NYC. There hSun raises event MASE relative to calendar in {n_hsun_cal} of 12 local model/step cells ({n_hsun_cal_c} of these rises consistent across both modes and leave-one-family-out subsets), "
           f"Rph in {n_rph_cal} ({n_rph_cal_c} consistent rises) and RpH in {n_rpH_cal} ({n_rpH_cal_c} consistent rise); "
           f"Rph is lower than pooled day in {n_rph_add} of 12 cells, while RpH is higher than typed day in {n_rpH_add}. "
           f"On the NYC ordinary sample, by contrast, the three designs lower MASE relative to calendar in {no_counts[0]}, {no_counts[1]} and {no_counts[2]} of 12 cells. "
           "So hSun is associated with higher NYC event-window MASE but lower ordinary-day MASE, whereas in India both mostly fall; with two observances and two related modes this is a bounded robustness check, and the mechanism is not identified. "
           f"RpH minus Rph has the same sign as typed minus pooled day in {same_n} of 12 NYC cells, the opposite sign in {opp_n} and ties in {tie_n} (Stable LightGBM gives identical typed and pooled forecasts). "
           f"Under replacing, India and NYC agree in sign in {cross_same} of 12 local model/lead cells, are opposite in {cross_opp} and tie in {cross_tie}. ")

text = v6
applied = []
for label, old, new in E:
    n = text.count(old)
    if n != 1:
        sys.exit(f"edit {label}: expected 1 occurrence, found {n}")
    text = text.replace(old, new)
    applied.append(label)
text = text.replace("__NYC_PLACEHOLDER__", nyc_par)
assert "__NYC_PLACEHOLDER__" not in text

# ---------- new appendix tables ----------
def mase_table(title, b, h):
    t = [title, "", "| Model | " + " | ".join(n for _, n in ARMS) + " |", "| --- |" + " --- |" * len(ARMS)]
    for m in LOCAL:
        t.append(f"| {NAMES[m]} | " + " | ".join(f5(b[(m, a, h)]) for a, _ in ARMS) + " |")
    return "\n".join(t)


def contrast_table(title, rows, cols, step, keys):
    t = [title, "", "| Model | Contrast | Balanced | " + " | ".join(c for c, _ in cols) + " | LOFO range | Label |",
         "| --- | --- | --- |" + " --- |" * len(cols) + " --- | --- |"]
    for m in LOCAL:
        for new, ref in keys:
            r = next(x for x in rows if x["model"] == m and x["contrast"] == f"{new} - {ref}" and x[step[0]] == step[1])
            t.append(f"| {NAMES[m]} | {SHORT[new]} − {SHORT[ref]} | {f5(r['balanced'])} | " + " | ".join(f5(r[c]) for _, c in cols)
                     + f" | {f5(r['lofo_min'])} to {f5(r['lofo_max'])} | {r['label']} |")
    return "\n".join(t)


KEYS = [("sunday_day", "pooled_day5"), ("replace_pooled", "pooled_day5"), ("replace_typed", "day5"), ("replace_typed", "replace_pooled")]
a6 = mase_table("Table A6. Ziel adaptations on the document-aligned Indian festival windows: local-model lead-1 MASE. The first three columns are recomputed and equal Table 1.", ib, 1)
a7 = contrast_table("Table A7. Indian lead-1 contrasts for the Ziel adaptations. Negative favours the first arm. Label: consistent = same sign in both years and every leave-one-family-out subset; negligible = absolute value below 0.005; otherwise unstable (registered rule).",
                    IC, [("2024", "year_2024"), ("2025", "year_2025")], ("horizon", "1"), KEYS)
a8 = mase_table("Table A8. Ziel adaptations on NYC event windows: decision lead 1 (model step 8), local-model MASE. The first three columns are recomputed and equal Table 4.", nb, 8)
a9 = contrast_table("Table A9. NYC decision-lead-1 contrasts for the Ziel adaptations. Negative favours the first arm. Label as in Table A7, with the two modes in place of the two years.",
                    NC, [("Bus", "mode_MTA_Bus"), ("Subway", "mode_MTA_Subway")], ("decision_lead", "1"), KEYS)
for m in LOCAL:  # Table A8 reference columns equal v6 Table 4
    row = next(l for l in v6.split("Table 4.")[1].splitlines() if l.startswith(f"| {NAMES[m]} |"))
    cells = [c.strip() for c in row.strip("|").split("|")]
    for (arm, _), cell in zip(ARMS[:3], cells[1:4]):
        assert f5(nb[(m, arm, 8)]) == cell, (m, arm, cell)
anchor = "All leads of Tables A4–A5 and the NYC cells are in the supplement files reanalysis_*.csv."
text = text.replace(anchor, anchor + "\n\n" + "\n\n".join([a6, a7, a8, a9]) +
                    "\n\nAll leads, both cohorts and every registered contrast of Tables A6–A9 are in the supplement files ziel_*.csv.", 1)
applied.append("appendix A6-A9")

# ---------- v6 tables unchanged ----------
def tables(md):
    return re.findall(r"(?m)^Table [0-9A]+[0-9]*\..*?(?=\n\n(?!\|))", md, flags=re.S)
v6_tables = {t.split(".")[0]: t for t in tables(v6)}
v7_tables = {t.split(".")[0]: t for t in tables(text)}
for k, t in v6_tables.items():
    assert v7_tables.get(k) == t, f"v6 table changed: {k}"
assert {"Table A6", "Table A7", "Table A8", "Table A9"} <= set(v7_tables)

OUT.mkdir(parents=True, exist_ok=False)
shutil.copytree(V6 / "figures", OUT / "figures")
shutil.copytree(V6 / "supplement", OUT / "supplement")
copies = {}
for prefix, d in [("ziel_india_hsun", I1), ("ziel_india_replacing", I2), ("ziel_nyc", NY)]:
    for f in sorted(d.glob("*.csv")):
        dest = OUT / "supplement" / f"{prefix}_{f.name}"
        shutil.copy2(f, dest)
        copies[str(dest.relative_to(ROOT))] = sha(f)
(OUT / "MANUSCRIPT.md").write_text(text)

docx = OUT / "Integrated_Review_Binay_Verma_v7.docx"
subprocess.run(["pandoc", str(OUT / "MANUSCRIPT.md"), "-o", str(docx), "--resource-path", str(OUT)], check=True)
subprocess.run(["soffice", "-env:UserInstallation=file:///tmp/tsfm-integrated-v7-lo", "--headless", "--convert-to", "pdf",
                "--outdir", str(OUT), str(docx)], check=True, capture_output=True)

build = {"created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "status": "Internal review draft v7; not independently reviewed or submission-ready.",
         "base": {"manuscript/integrated_review_v6/MANUSCRIPT.md": sha(V6 / "MANUSCRIPT.md")},
         "edits_applied": applied, "v6_tables_unchanged": sorted(v6_tables),
         "inputs": {str(p.relative_to(ROOT)): sha(p) for d in (I1, I2, NY) for p in sorted(d.glob("*"))} | {str(SG.relative_to(ROOT)): sha(SG)},
         "supplement_copies": copies,
         "outputs": {p.name: sha(p) for p in [OUT / "MANUSCRIPT.md", docx]},
         "renderer": "pandoc + LibreOffice (same as v6)",
         "revision": "Rebuilt after an internal fresh-eyes check of the first v7 build (commit f030451): push status, reproduction bound, NYC and ordinary-cohort wording, Ziel findings and scope sentences corrected; numbers unchanged."}
json.dump(build, open(OUT / "build.json", "w"), indent=1)
print(json.dumps({k: build[k] for k in ("edits_applied", "v6_tables_unchanged")}, indent=1))
print(dict(same_i=same_i, same_n=same_n, opp_n=opp_n, tie_n=tie_n, cross=(cross_same, cross_opp, cross_tie)))
