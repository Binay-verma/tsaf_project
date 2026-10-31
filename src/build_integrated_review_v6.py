"""Build integrated review v6 from the unchanged v5 manuscript.

Applies claim-ledger revisions R1-R8 (review/journal_seven_tasks_20261031_v1/SEVEN_TASK_LEDGER.md)
as exact, asserted text replacements. Every new number is computed here from committed CSVs.
v5 is never modified. Run from the repository root: python src/build_integrated_review_v6.py
"""
import csv, datetime, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V5 = ROOT / "manuscript/integrated_review_v5"
OUT = ROOT / "manuscript/integrated_review_v6"
RA = ROOT / "review/journal_seven_tasks_20261031_v1"
NAMES = {"ridge": "Rich Ridge", "sarimax": "SARIMAX", "lightgbm": "Stable LightGBM",
         "lightgbm_capacity2": "Tree leaf minimum 2", "chronos": "Chronos-2", "timesfm": "TimesFM-3"}
ARMS = {"calendar": "Calendar", "day5": "Typed day", "pooled_day5": "Pooled day",
        "window5": "Typed window", "pooled_window5": "Pooled window"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rows(name):
    return list(csv.DictReader(open(RA / name)))


def f5(x):
    return f"{float(x):.5f}"


# ---------- numbers from the registered re-analysis ----------
res = json.load(open(RA / "descriptive_reanalysis_result.json"))
B = rows("B_cluster_summary.csv")
C = rows("C_native_cluster_coverage.csv")
A = res["A"]["summary"]["typed_minus_pooled"]
n_cells = len(B)
TC = json.load(open(RA / "tie_correction_v2.json"))  # corrects exact-tie handling; original outputs preserved
years_disagree = TC["B_years"]["opposite_sign"]
year_ties = TC["B_years"]["exact_tie_in_either_year"]
lofo_flip = res["B_overall"]["cells_with_any_leave_one_family_out_sign_flip"]
src_opposite = TC["A_typed_minus_pooled"]["opposite_sign"]
src_same = TC["A_typed_minus_pooled"]["same_sign"]
src_ties = TC["A_typed_minus_pooled"]["exact_tie_in_either"]
tfm_opposite = TC["A_typed_minus_pooled"]["timesfm_opposite"]
inv = res["B_inventory"]
lead1 = [r for r in C if r["lead"] == "1"]
below = sum(int(r["clusters_below_0.8"]) for r in lead1)
defined = sum(int(r["clusters_defined"]) for r in lead1)
tcal = next(r for r in lead1 if r["model"] == "timesfm" and r["arm"] == "calendar")
crossings = sum(int(r["common_crossing_pairs"]) for r in C)
invalid = sum(int(r["invalid80_rows"]) for r in C)
D = res["D"]
D_ties = D["rows"] - D["pooled_better"] - D["typed_better"]
sar = next(r for r in B if r["model"] == "sarimax" and r["representation"] == "day" and r["lead"] == "1")
assert float(sar["year_2024"]) < 0 and float(sar["year_2025"]) < 0 and float(sar["lofo_max"]) < 0
tfm = next(r for r in B if r["model"] == "timesfm" and r["representation"] == "day" and r["lead"] == "1")
assert int(tfm["clusters_pooled_better"]) > int(tfm["clusters_typed_better"])

# ---------- edits ----------
E = [
 ("R3 title",
  "# When does pooling sparse event information help forecasting? Matched representations, calendar corrections and cross-source evidence",
  "# Typed versus pooled festival covariates in foundation and local forecasting models: matched controls, calendar corrections and unstable orderings"),
 ("status",
  "**Integrated research draft for professor review. Not submitted or submission-ready.**",
  "**Integrated research draft for professor review, version 6. Not submitted or submission-ready.** Version 6 applies the internal claim-ledger revisions of 31 October 2026 to version 5; all version 5 result tables are unchanged."),
 ("R2 abstract",
  "A pre-acquisition registered NYC replication adds two later holiday occurrences",
  "An NYC replication, committed before its evaluation records were acquired, adds two later holiday occurrences"),
 ("R3 abstract",
  "These are complete registered contrast ranges, not selected improvements or sampling intervals.",
  "These are complete registered contrast ranges, not selected improvements or sampling intervals. "
  f"The preferred representation is not stable: within India the typed-minus-pooled sign is opposite between the two event years in {years_disagree} of {n_cells} model/representation/lead cells (one more is an exact tie), "
  f"and opposite between India and NYC in {src_opposite} of {n_cells} cells ({src_ties} tie), including all {tfm_opposite} TimesFM-3 cells."),
 ("R3 abstract end",
  "The evidence qualifies when representations help; it does not introduce a new architecture or establish causal event effects.",
  "The evidence documents where the ordering holds and where it reverses; it does not introduce a new architecture or establish causal event effects."),
 ("R5 closest work",
  "Indian moving-holiday regression [3], covariate-uncertainty evaluation [4] and sample/proxy leakage analysis [5] are close antecedents.",
  "Indian moving-holiday regression [3], covariate-uncertainty evaluation [4] and sample/proxy leakage analysis [5] are close antecedents. "
  "The typed-versus-pooled choice itself is established in load forecasting: Ziel [9] compared one shared holiday dummy, grouped dummies and a separate dummy for each holiday for German load, "
  "and found that separate dummies did not generally improve on a single dummy, with univariate results mixed by holiday type. Arora and Taylor [10] treat special days with rule-based seasonal ARMA models. "
  "What is examined here is how that choice behaves through foundation-model covariate channels under a fixed channel budget with zero and placebo controls."),
 ("R1 effective units",
  "Nearby days, states and leads are correlated, not independent event replications.",
  f"They cover {inv['unique_target_dates']} distinct target dates and {inv['family_year_clusters']} family/year clusters; the clusters, not rows, are the effective event units. "
  "Nearby days, states and leads are correlated, not independent event replications."),
 ("R2 NYC",
  "The protocol was publicly committed before these new evaluation records were acquired.",
  "The protocol was committed (e7d9423, 20:23:38 UTC on 30 October 2026) before these new evaluation records were acquired (20:24:51 UTC). The public push time of that commit has not been independently verified."),
 ("R4/R6 year dependence",
  "These are different estimands; an old/new macro-score difference must not be attributed entirely to corrected festival features.",
  "These are different estimands; an old/new macro-score difference must not be attributed entirely to corrected festival features.\n\n"
  f"Table A4 splits the lead-1 contrasts by event year and family. Across all {n_cells} model/representation/lead cells, the 2024 and 2025 contrasts have opposite signs in {years_disagree}, with {year_ties} further exact tie, "
  f"and leaving out one family flips the balanced sign in {lofo_flip}. A few orderings persist: SARIMAX day flags at lead 1 favour separate identities in both years and under every leave-one-family-out "
  f"subset, and TimesFM-3 day flags at lead 1 favour pooling in {tfm['clusters_pooled_better']} of {tfm['family_year_clusters']} family/year clusters. "
  "This descriptive split was registered before it was computed, but it uses previously inspected forecasts; the persistent orderings are expectations for future confirmation, not established effects."),
 ("R4 NYC reversal",
  "Two parking-observance occurrences and two related modes support a bounded robustness check, not universal mechanism identification or a pooled cross-country treatment effect.",
  "Two parking-observance occurrences and two related modes support a bounded robustness check, not universal mechanism identification or a pooled cross-country treatment effect. "
  f"Comparing signs cell by cell, India and NYC agree in {src_same} of {n_cells} typed-minus-pooled cells, are opposite in {src_opposite} and tie in {src_ties} (Stable LightGBM day flags give identical NYC forecasts); TimesFM-3 favours pooling in India and separate identities in NYC in all {tfm_opposite} of its cells. "
  f"Within NYC, {D['pooled_better']} of {D['rows']} family/mode/step cells favour pooling, {D['typed_better']} favour separate identities and {D_ties} tie."),
 ("R7 coverage dispersion",
  "Native interval quality and point MASE are different criteria.",
  "Native interval quality and point MASE are different criteria. "
  f"Means hide dispersion across event clusters: at lead 1, family/year coverage falls below 0.80 in {below} of {defined} foundation-model cluster/arm cells (Table A5); "
  f"for TimesFM-3 calendar it ranges from {float(tcal['coverage_min']):.3f} to {float(tcal['coverage_max']):.3f}. "
  f"This cohort has {crossings} common-grid crossing pairs and {invalid} invalid interval endpoints."),
 ("R5 limits",
  "Generic encodings and sparse pooling have close prior work;",
  "Generic encodings, sparse pooling and pooled-versus-separate holiday dummies [9] have close prior work;"),
 ("R8 data statement",
  "Local environments, model weights/caches and restricted or unresolved external raw archives are excluded.",
  "Local environments and model weights/caches are excluded. The GRID-INDIA/POSOCO compilation curated by Robbie Andrew, whose reuse terms are unresolved, is currently present in the public repository "
  "(data/external/POSOCO_data.csv), as are derived files containing its values; its sharing status awaits the curator's reply. The Hunt and Bloomfield and SASEA sources are CC BY 4.0. NESO raw archives are outside Git."),
 ("R5 references",
  "[8] Romano, Patterson and Candès (2019). Conformalized Quantile Regression. arXiv:1905.03222v1. https://arxiv.org/abs/1905.03222",
  "[8] Romano, Patterson and Candès (2019). Conformalized Quantile Regression. arXiv:1905.03222v1. https://arxiv.org/abs/1905.03222\n\n"
  "[9] Ziel (2018). Modeling public holidays in load forecasting: a German case study. Journal of Modern Power Systems and Clean Energy 6(2), 191–207. https://doi.org/10.1007/s40565-018-0385-5\n\n"
  "[10] Arora and Taylor (2018). Rule-based autoregressive moving average models for forecasting load on special days: A case study for France. European Journal of Operational Research 266(1), 259–268. https://doi.org/10.1016/j.ejor.2017.08.056"),
]

# ---------- new appendix tables ----------
t4 = ["Table A4. Indian typed-minus-pooled MASE at lead 1 by event year and family. Positive favours pooling. Clusters are family/year groups; they share states, weather and source vintage and are not independent replications. LOFO: leave-one-family-out balanced contrast. Exact ties are not counted in the cluster column.",
      "", "| Model | Rep. | Balanced | 2024 | 2025 | Pooled / typed clusters | LOFO range |",
      "| --- | --- | --- | --- | --- | --- | --- |"]
for r in B:
    if r["lead"] != "1":
        continue
    t4.append(f"| {NAMES[r['model']]} | {r['representation']} | {f5(r['balanced'])} | {f5(r['year_2024'])} | {f5(r['year_2025'])} | "
              f"{r['clusters_pooled_better']} / {r['clusters_typed_better']} | {f5(r['lofo_min'])} to {f5(r['lofo_max'])} |")
t5 = ["Table A5. Native 80% coverage across the ten Indian family/year clusters at lead 1 (unmodified intervals).",
      "", "| Model | Arm | Minimum | Maximum | Clusters below 0.80 |", "| --- | --- | --- | --- | --- |"]
for r in lead1:
    t5.append(f"| {NAMES[r['model']]} | {ARMS[r['arm']]} | {float(r['coverage_min']):.3f} | {float(r['coverage_max']):.3f} | {r['clusters_below_0.8']} of {r['clusters_defined']} |")
anchor = "The supplementary source tables retain all leads, both cohorts, both feature views, every control and every registered pair."
E.append(("R6 appendix tables", anchor, "\n".join(t4) + "\n\n" + "\n".join(t5) + "\n\nAll leads of Tables A4–A5 and the NYC cells are in the supplement files reanalysis_*.csv.\n\n" + anchor))

text = (V5 / "MANUSCRIPT.md").read_text()
applied = []
for label, old, new in E:
    n = text.count(old)
    if n != 1:
        sys.exit(f"edit {label}: expected 1 occurrence, found {n}")
    text = text.replace(old, new)
    applied.append(label)

# v5 tables must be unchanged
def tables(md):
    return re.findall(r"(?m)^Table [0-9A]+[0-9]*\..*?(?=\n\n(?!\|))", md, flags=re.S)
v5_tables = {t.split(".")[0]: t for t in tables((V5 / "MANUSCRIPT.md").read_text())}
v6_tables = {t.split(".")[0]: t for t in tables(text)}
for k, t in v5_tables.items():
    assert v6_tables.get(k) == t, f"v5 table changed: {k}"

OUT.mkdir(parents=True, exist_ok=False)
shutil.copytree(V5 / "figures", OUT / "figures")
shutil.copytree(V5 / "supplement", OUT / "supplement")
for name, src in [("reanalysis_cross_source.csv", "A_cross_source_cells.csv"), ("reanalysis_india_clusters.csv", "B_family_year_clusters.csv"),
                  ("reanalysis_india_cluster_summary.csv", "B_cluster_summary.csv"), ("reanalysis_native_cluster_coverage.csv", "C_native_cluster_coverage.csv"),
                  ("reanalysis_nyc_cells.csv", "D_nyc_cells.csv")]:
    shutil.copy2(RA / src, OUT / "supplement" / name)
(OUT / "MANUSCRIPT.md").write_text(text)

docx = OUT / "Integrated_Review_Binay_Verma_v6.docx"
subprocess.run(["pandoc", str(OUT / "MANUSCRIPT.md"), "-o", str(docx), "--resource-path", str(OUT)], check=True)
subprocess.run(["soffice", "-env:UserInstallation=file:///tmp/tsfm-integrated-v6-lo", "--headless", "--convert-to", "pdf",
                "--outdir", str(OUT), str(docx)], check=True, capture_output=True)

build = {"created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "status": "Internal review draft v6; not independently reviewed or submission-ready.",
         "base": {"manuscript/integrated_review_v5/MANUSCRIPT.md": sha(V5 / "MANUSCRIPT.md")},
         "edits_applied": applied, "v5_tables_unchanged": sorted(v5_tables),
         "inputs": {str(p.relative_to(ROOT)): sha(p) for p in [RA / "descriptive_reanalysis_result.json", RA / "B_cluster_summary.csv",
                    RA / "C_native_cluster_coverage.csv", RA / "registration_descriptive_reanalysis.json"]},
         "outputs": {p.name: sha(p) for p in [OUT / "MANUSCRIPT.md", docx]},
         "renderer": "pandoc + LibreOffice (differs from the v4/v5 python-docx builder styling)"}
json.dump(build, open(OUT / "build.json", "w"), indent=1)
print(json.dumps({k: build[k] for k in ("edits_applied", "v5_tables_unchanged")}, indent=1))
