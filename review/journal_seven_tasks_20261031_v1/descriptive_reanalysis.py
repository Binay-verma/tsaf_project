"""Registered descriptive re-analysis (see registration_descriptive_reanalysis.json).

Uses only already-inspected retrospective forecast files. Standard library only.
Run from repository root:  python review/journal_seven_tasks_20261031_v1/descriptive_reanalysis.py
"""
import csv, json, hashlib, math, sys
from collections import defaultdict
from statistics import mean

D = "review/journal_seven_tasks_20261031_v1"
REG = json.load(open(f"{D}/registration_descriptive_reanalysis.json"))
for k, v in REG["inputs"].items():
    h = hashlib.sha256(open(v["path"], "rb").read()).hexdigest()
    if h != v["sha256"]:
        sys.exit(f"input hash mismatch for {k}")

MODELS = ["ridge", "sarimax", "lightgbm", "lightgbm_capacity2", "chronos", "timesfm"]
REPS = {"day": ("day5", "pooled_day5"), "window": ("window5", "pooled_window5")}
NEAR = 0.005
out = {"registration": f"{D}/registration_descriptive_reanalysis.json"}


def sign(x, band=0.0):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "undefined"
    if abs(x) < band:
        return "near_zero"
    return "pooled_better" if x > 0 else "typed_better"


# ---------- balanced metrics ----------
def load_bal(path, leadcol, version=None):
    m = {}
    for r in csv.DictReader(open(path)):
        if version and r.get("version") != version:
            continue
        m[(r["model"], r["arm"], int(r[leadcol]))] = float(r["MASE"])
    return m

india = load_bal(REG["inputs"]["india_metrics"]["path"], "horizon", "document_aligned")
nyc = load_bal(REG["inputs"]["nyc_metrics"]["path"], "decision_lead")

# ---------- A: cross-source sign agreement ----------
A = []
for mo in MODELS:
    for rep, (ta, pa) in REPS.items():
        for ld in (1, 7, 14):
            row = {"model": mo, "representation": rep, "decision_lead": ld}
            for src, m in (("india", india), ("nyc", nyc)):
                cal = m[(mo, "calendar", ld)]
                row[f"{src}_typed_minus_pooled"] = m[(mo, ta, ld)] - m[(mo, pa, ld)]
                row[f"{src}_typed_minus_calendar"] = m[(mo, ta, ld)] - cal
                row[f"{src}_pooled_minus_calendar"] = m[(mo, pa, ld)] - cal
            A.append(row)

def agree(rows, key, band):
    s = [(sign(r[f"india_{key}"], band), sign(r[f"nyc_{key}"], band)) for r in rows]
    decided = [x for x in s if "near_zero" not in x]
    return {"cells": len(s), "both_decided": len(decided),
            "same_sign": sum(a == b for a, b in decided),
            "opposite_sign": sum(a != b for a, b in decided),
            "near_zero_in_either": len(s) - len(decided)}

summA = {}
for key in ("typed_minus_pooled", "typed_minus_calendar", "pooled_minus_calendar"):
    summA[key] = {"no_band": agree(A, key, 0.0), f"band_{NEAR}": agree(A, key, NEAR)}
    for mo in MODELS:
        summA[key][mo] = agree([r for r in A if r["model"] == mo], key, 0.0)
# sign of improvement over calendar (negative = event information helps)
for src in ("india", "nyc"):
    for key in ("typed_minus_calendar", "pooled_minus_calendar"):
        v = [r[f"{src}_{key}"] for r in A]
        summA[f"{src}_{key}_count_below_zero"] = sum(x < 0 for x in v)
out["A"] = {"summary": summA}
with open(f"{D}/A_cross_source_cells.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(A[0].keys())); w.writeheader(); w.writerows(A)

# ---------- B: India cluster dependence ----------
P = [r for r in csv.DictReader(open(REG["inputs"]["india_predictions"]["path"]))
     if r["version"] == "document_aligned"]
cell = defaultdict(list)  # (model, arm, h, family, year, state) -> MASE list
dates, episodes = set(), set()
for r in P:
    cell[(r["model"], r["arm"], int(r["horizon"]), r["family"], r["year"], r["state"])].append(float(r["MASE"]))
    dates.add(r["date"]); episodes.add((r["state"], r["date"]))

def fam_year(mo, arm, h, fam, yr):
    vals = [mean(v) for (a, b, c, d, e, s), v in cell.items() if (a, b, c, d, e) == (mo, arm, h, fam, yr)]
    return mean(vals) if vals else None

FAMS = sorted({k[3] for k in cell}); YEARS = sorted({k[4] for k in cell})

def balanced(mo, arm, h, fams=FAMS, years=YEARS):
    fv = []
    for fam in fams:
        yv = [fam_year(mo, arm, h, fam, y) for y in years]
        yv = [x for x in yv if x is not None]
        if yv:
            fv.append(mean(yv))
    return mean(fv)

recon_max = 0.0
for mo in MODELS:
    for arm in ("calendar", "day5", "pooled_day5", "window5", "pooled_window5", "zero5", "placebo_day5", "placebo_window5"):
        for h in (1, 7, 14):
            recon_max = max(recon_max, abs(balanced(mo, arm, h) - india[(mo, arm, h)]))
out["B_reconstruction_max_abs_diff"] = recon_max
if recon_max > 1e-12:
    json.dump(out, open(f"{D}/descriptive_reanalysis_result.json", "w"), indent=1)
    sys.exit(f"Reconstruction failed: {recon_max}")

Brows, Bsum = [], []
for mo in MODELS:
    for rep, (ta, pa) in REPS.items():
        for h in (1, 7, 14):
            fy = {}
            for fam in FAMS:
                for y in YEARS:
                    t, p = fam_year(mo, ta, h, fam, y), fam_year(mo, pa, h, fam, y)
                    if t is None:
                        continue
                    fy[(fam, y)] = t - p
                    Brows.append({"model": mo, "representation": rep, "lead": h, "family": fam,
                                  "year": y, "typed_minus_pooled": t - p})
            lofo = [balanced(mo, ta, h, [f for f in FAMS if f != x]) - balanced(mo, pa, h, [f for f in FAMS if f != x]) for x in FAMS]
            loyo = [balanced(mo, ta, h, FAMS, [y]) - balanced(mo, pa, h, FAMS, [y]) for y in YEARS]
            full = india[(mo, ta, h)] - india[(mo, pa, h)]
            Bsum.append({"model": mo, "representation": rep, "lead": h, "balanced": full,
                         "family_year_clusters": len(fy),
                         "clusters_pooled_better": sum(v > 0 for v in fy.values()),
                         "clusters_typed_better": sum(v < 0 for v in fy.values()),
                         "lofo_min": min(lofo), "lofo_max": max(lofo),
                         "lofo_sign_flips": sum((x > 0) != (full > 0) for x in lofo),
                         "year_2024": loyo[0], "year_2025": loyo[1],
                         "years_disagree_in_sign": (loyo[0] > 0) != (loyo[1] > 0)})
out["B_inventory"] = {"unique_target_dates": len(dates), "state_date_episodes": len(episodes),
                      "families": FAMS, "years": YEARS,
                      "family_year_clusters": len({(k[3], k[4]) for k in cell}),
                      "family_state_year_cells": len({(k[3], k[4], k[5]) for k in cell})}
out["B_overall"] = {
    "cells": len(Bsum),
    "cells_where_the_two_years_disagree_in_sign": sum(r["years_disagree_in_sign"] for r in Bsum),
    "cells_with_any_leave_one_family_out_sign_flip": sum(r["lofo_sign_flips"] > 0 for r in Bsum)}
for name, rows in (("B_family_year_clusters.csv", Brows), ("B_cluster_summary.csv", Bsum)):
    with open(f"{D}/{name}", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

# ---------- C: native interval cluster dispersion ----------
N = [r for r in csv.DictReader(open(REG["inputs"]["india_native_cases"]["path"]))
     if r["version"] == "document_aligned" and r["model"] in ("chronos", "timesfm")]
nc = defaultdict(list)
for r in N:
    nc[(r["model"], r["arm"], int(r["horizon"]), r["family"], r["year"], r["state"])].append(r)

def fnum(x):
    try:
        v = float(x); return None if math.isnan(v) else v
    except (TypeError, ValueError):
        return None

Crows = []
for mo in ("chronos", "timesfm"):
    for arm in ("calendar", "day5", "pooled_day5", "window5", "pooled_window5"):
        for h in (1, 7, 14):
            covs, inval, cross, undefined = [], 0, 0, 0
            for fam in FAMS:
                for y in YEARS:
                    sv, und = [], False
                    for (a, b, c, d, e, s), rows in nc.items():
                        if (a, b, c, d, e) != (mo, arm, h, fam, y):
                            continue
                        vals = [fnum(r["coverage80"]) for r in rows]
                        inval += sum(1 for r in rows if r["invalid80"] not in ("0", "False", "false", "", "0.0"))
                        cross += sum(int(float(r["common_crossings"] or 0)) for r in rows)
                        if any(v is None for v in vals):
                            und = True
                        else:
                            sv.append(mean(vals))
                    if not sv and not und:
                        continue
                    if und:
                        undefined += 1
                    else:
                        covs.append(mean(sv))
            Crows.append({"model": mo, "arm": arm, "lead": h, "clusters_defined": len(covs),
                          "clusters_undefined": undefined,
                          "coverage_min": min(covs) if covs else None,
                          "coverage_max": max(covs) if covs else None,
                          "clusters_below_0.8": sum(c < 0.8 for c in covs),
                          "invalid80_rows": inval, "common_crossing_pairs": cross})
with open(f"{D}/C_native_cluster_coverage.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(Crows[0].keys())); w.writeheader(); w.writerows(Crows)
out["C_rows"] = len(Crows)

# ---------- D: NYC cells ----------
Drows = []
for r in csv.DictReader(open(REG["inputs"]["nyc_contrasts_series_year"]["path"])):
    for rep, (ta, pa) in REPS.items():
        if r["arm"] == ta and r["reference"] == pa:
            v = float(r["MASE_change"])
        elif r["arm"] == pa and r["reference"] == ta:
            v = -float(r["MASE_change"])
        else:
            continue
        Drows.append({"model": r["model"], "representation": rep, "family": r["family"],
                      "series": r["state"], "model_step": int(r["horizon"]), "typed_minus_pooled": v})
with open(f"{D}/D_nyc_cells.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(Drows[0].keys())); w.writeheader(); w.writerows(Drows)
out["D"] = {"rows": len(Drows), "pooled_better": sum(r["typed_minus_pooled"] > 0 for r in Drows),
            "typed_better": sum(r["typed_minus_pooled"] < 0 for r in Drows)}

json.dump(out, open(f"{D}/descriptive_reanalysis_result.json", "w"), indent=1)
print(json.dumps(out, indent=1))
