"""Correction v2 to the registered descriptive re-analysis (original outputs preserved unchanged).

Defect found 31 Oct 2026: descriptive_reanalysis.py classified an exact zero contrast as 'typed better'
(and the year/leave-one-family-out comparisons used (x > 0) != (y > 0)), so exact ties were counted
as sign disagreements. Here an exact tie (|x| < 1e-12) is its own category. No other rule changes.
"""
import csv, json

D = "review/journal_seven_tasks_20261031_v1"
EPS = 1e-12


def s(x):
    x = float(x)
    return 0 if abs(x) < EPS else (1 if x > 0 else -1)


A = list(csv.DictReader(open(f"{D}/A_cross_source_cells.csv")))
B = list(csv.DictReader(open(f"{D}/B_cluster_summary.csv")))
out = {"defect": __doc__.strip(), "original_outputs_preserved": True}
for key in ("typed_minus_pooled", "typed_minus_calendar", "pooled_minus_calendar"):
    pairs = [(s(r[f"india_{key}"]), s(r[f"nyc_{key}"]), r["model"]) for r in A]
    out[f"A_{key}"] = {"cells": len(pairs), "same_sign": sum(a == b != 0 for a, b, _ in pairs),
                       "opposite_sign": sum(a * b == -1 for a, b, _ in pairs),
                       "exact_tie_in_either": sum(a == 0 or b == 0 for a, b, _ in pairs),
                       "timesfm_opposite": sum(a * b == -1 for a, b, m in pairs if m == "timesfm")}
yr = [(s(r["year_2024"]), s(r["year_2025"])) for r in B]
out["B_years"] = {"cells": len(yr), "opposite_sign": sum(a * b == -1 for a, b in yr),
                  "exact_tie_in_either_year": sum(a == 0 or b == 0 for a, b in yr),
                  "tie_cells": [f"{r['model']}/{r['representation']}/lead{r['lead']}" for r in B
                                if s(r["year_2024"]) == 0 or s(r["year_2025"]) == 0]}
lofo_ties = [r for r in B if s(r["lofo_min"]) == 0 or s(r["lofo_max"]) == 0 or s(r["balanced"]) == 0]
out["B_lofo"] = {"cells_with_sign_flip": sum(int(r["lofo_sign_flips"]) > 0 for r in B),
                 "cells_with_exact_zero_in_lofo_or_balanced": len(lofo_ties),
                 "note": "Flip count unaffected unless a LOFO or balanced value is an exact zero."}
json.dump(out, open(f"{D}/tie_correction_v2.json", "w"), indent=1)
print(json.dumps(out, indent=1))
