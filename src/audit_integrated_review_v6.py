"""Separate audit of manuscript v6: every added number is recomputed from case-level files,
not from the builder's intermediate summaries; all non-edited v5 text must be unchanged."""
import csv, difflib, json, re, sys
from collections import defaultdict
from statistics import mean
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
v5 = (ROOT / "manuscript/integrated_review_v5/MANUSCRIPT.md").read_text()
v6 = (ROOT / "manuscript/integrated_review_v6/MANUSCRIPT.md").read_text()
fail = []

# 1. Only paragraphs touched by the registered edits differ.
p5 = [p.strip() for p in v5.split("\n\n") if p.strip()]
p6set = {p.strip() for p in v6.split("\n\n")}
removed = [p for p in p5 if p not in p6set]
expected_changed_prefixes = ["# When does pooling", "**Integrated research draft", "Sparse events create", "Kreusel et al. [1]",
    "The resulting 528", "The protocol was publicly", "The canonical MTA", "The full event contrast", "NYC's complete event",
    "Both foundations are compared", "The named-date correction", "Completed code, protocols", "[8] Romano", "The supplementary source tables"]
for p in removed:
    if not any(p.startswith(x) for x in expected_changed_prefixes):
        fail.append("unexpected changed paragraph: " + p[:80])

# 2. Recompute India cluster numbers from case-level predictions.
P = [r for r in csv.DictReader(open(ROOT / "results/calendar_recenter_recovery_v1/analysis/breadth/event_window/predictions_compared.csv"))
     if r["version"] == "document_aligned"]
cell = defaultdict(list)
for r in P:
    cell[(r["model"], r["arm"], int(r["horizon"]), r["family"], r["year"], r["state"])].append(float(r["MASE"]))
fy = defaultdict(list)
for (m, a, h, f, y, s), v in cell.items():
    fy[(m, a, h, f, y)].append(mean(v))
fy = {k: mean(v) for k, v in fy.items()}
fams = sorted({k[3] for k in fy}); years = sorted({k[4] for k in fy})
def bal(m, a, h, F=fams, Y=years):
    return mean(mean(fy[(m, a, h, f, y)] for y in Y if (m, a, h, f, y) in fy) for f in F if any((m, a, h, f, y) in fy for y in Y))
pairs = {"day": ("day5", "pooled_day5"), "window": ("window5", "pooled_window5")}
models = ["ridge", "sarimax", "lightgbm", "lightgbm_capacity2", "chronos", "timesfm"]
yd = lf = 0
lead1 = {}
for m in models:
    for rep, (t, p) in pairs.items():
        for h in (1, 7, 14):
            full = bal(m, t, h) - bal(m, p, h)
            y24 = bal(m, t, h, fams, ["2024"]) - bal(m, p, h, fams, ["2024"])
            y25 = bal(m, t, h, fams, ["2025"]) - bal(m, p, h, fams, ["2025"])
            yd += (y24 > 1e-12 and y25 < -1e-12) or (y24 < -1e-12 and y25 > 1e-12)
            lofo = [bal(m, t, h, [g for g in fams if g != x]) - bal(m, p, h, [g for g in fams if g != x]) for x in fams]
            lf += any((x > 0) != (full > 0) for x in lofo)
            if h == 1:
                cl = [fy[(m, t, 1, f, y)] - fy[(m, p, 1, f, y)] for f in fams for y in years if (m, t, 1, f, y) in fy]
                lead1[(m, rep)] = (full, y24, y25, sum(c > 0 for c in cl), sum(c < 0 for c in cl), min(lofo), max(lofo))
def need(s):
    if s not in v6:
        fail.append("missing/incorrect text: " + s)
need(f"opposite between the two event years in {yd} of 36")
need(f"have opposite signs in {yd}, with 1 further exact tie")
need(f"leaving out one family flips the balanced sign in {lf}")
NAMES = {"ridge": "Rich Ridge", "sarimax": "SARIMAX", "lightgbm": "Stable LightGBM", "lightgbm_capacity2": "Tree leaf minimum 2", "chronos": "Chronos-2", "timesfm": "TimesFM-3"}
for (m, rep), v in lead1.items():
    need(f"| {NAMES[m]} | {rep} | {v[0]:.5f} | {v[1]:.5f} | {v[2]:.5f} | {v[3]} / {v[4]} | {v[5]:.5f} to {v[6]:.5f} |")

# 3. Cross-source signs from balanced metric files.
def balfile(path, col, ver=None):
    return {(r["model"], r["arm"], int(r[col])): float(r["MASE"]) for r in csv.DictReader(open(ROOT / path)) if ver is None or r["version"] == ver}
I = balfile("results/calendar_recenter_recovery_v1/analysis/breadth/event_window/metrics_balanced.csv", "horizon", "document_aligned")
N = balfile("results/mta_holiday_recovery_v1/analysis/event_window/metrics_balanced.csv", "decision_lead")
sg = lambda x: 0 if abs(x) < 1e-12 else (1 if x > 0 else -1)
prs = [(sg(I[(m, t, h)] - I[(m, p, h)]), sg(N[(m, t, h)] - N[(m, p, h)])) for m in models for t, p in pairs.values() for h in (1, 7, 14)]
opp = sum(a * b == -1 for a, b in prs); same = sum(a == b != 0 for a, b in prs); ties = sum(a == 0 or b == 0 for a, b in prs)
tfo = sum(((I[("timesfm", t, h)] - I[("timesfm", p, h)]) > 0) != ((N[("timesfm", t, h)] - N[("timesfm", p, h)]) > 0) for t, p in pairs.values() for h in (1, 7, 14))
need(f"opposite between India and NYC in {opp} of 36 cells ({ties} tie), including all {tfo} TimesFM-3 cells")
need(f"India and NYC agree in {same} of 36 typed-minus-pooled cells, are opposite in {opp} and tie in {ties}")

# 4. Native coverage from case-level interval file.
Q = [r for r in csv.DictReader(open(ROOT / "results/calendar_recenter_recovery_v1/analysis/breadth/event_window/native_uncertainty_cases.csv"))
     if r["version"] == "document_aligned" and r["horizon"] == "1" and r["model"] in ("chronos", "timesfm")
     and r["arm"] in ("calendar", "day5", "pooled_day5", "window5", "pooled_window5")]
cc = defaultdict(list)
for r in Q:
    cc[(r["model"], r["arm"], r["family"], r["year"], r["state"])].append(float(r["coverage80"]))
cf = defaultdict(list)
for (m, a, f, y, s), v in cc.items():
    cf[(m, a, f, y)].append(mean(v))
cf = {k: mean(v) for k, v in cf.items()}
below = sum(v < 0.8 for v in cf.values())
need(f"falls below 0.80 in {below} of {len(cf)} foundation-model cluster/arm cells")
tc = [v for (m, a, f, y), v in cf.items() if m == "timesfm" and a == "calendar"]
need(f"ranges from {min(tc):.3f} to {max(tc):.3f}")

result = {"status": "pass" if not fail else "fail", "failures": fail, "changed_v5_paragraphs": len(removed),
          "recomputed": {"years_disagree": yd, "lofo_flip": lf, "source_opposite": opp, "source_same": same, "source_ties": ties, "timesfm_opposite": tfo,
                         "coverage_below": below, "coverage_cells": len(cf), "table_A4_rows": len(lead1)}}
json.dump(result, open(ROOT / "manuscript/integrated_review_v6/independent_v6_audit.json", "w"), indent=1)
print(json.dumps(result, indent=1))
sys.exit(1 if fail else 0)
