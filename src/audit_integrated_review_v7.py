"""Recomputation audit of every new number in manuscript v7 (a second code path by the same author, not independent review).

Recomputes Tables A6-A9 and the counts quoted in the new text directly from the raw
prediction files (standard library only, a different code path from the registered
analysis), and checks that v6 text outside the asserted insertions is unchanged.
Run from the repository root: python src/audit_integrated_review_v7.py
"""
import csv, json, re, sys
from collections import defaultdict
from statistics import mean
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MS = (ROOT / "manuscript/integrated_review_v7/MANUSCRIPT.md").read_text()
V6 = (ROOT / "manuscript/integrated_review_v6/MANUSCRIPT.md").read_text()
LOCAL = ["ridge", "sarimax", "lightgbm", "lightgbm_capacity2"]
NAMES = {"Rich Ridge": "ridge", "SARIMAX": "sarimax", "Stable LightGBM": "lightgbm", "Tree leaf minimum 2": "lightgbm_capacity2"}
COL = {"Calendar": "calendar", "Typed day": "day5", "Pooled day": "pooled_day5", "hSun": "sunday_day", "Rph": "replace_pooled", "RpH": "replace_typed"}
SHORT = {"hSun": "sunday_day", "Rph": "replace_pooled", "RpH": "replace_typed", "pooled day": "pooled_day5", "typed day": "day5"}
problems = []


def rows_of(paths):
    out = []
    for p in paths:
        out += list(csv.DictReader(open(p)))
    return out


def india_rows():
    seen = {}
    for d in ["results/ziel_replacing_v1/event_window", "results/ziel_replacing_v2/event_window"]:
        for m in LOCAL:
            for r in csv.DictReader(open(ROOT / d / m / "predictions.csv")):
                k = (r["model"], r["arm"], r["family"], r["state"], r["year"], r["date"][:10], r["horizon"])
                e = abs(float(r["prediction"]) - float(r["actual"])) / float(r["mase_scale"])
                if k in seen and abs(seen[k][-1] - e) > 1e-12:
                    problems.append(("india reference arm differs between runs", k))
                seen[k] = (r["model"], r["arm"], r["family"], r["state"], r["year"], int(r["horizon"]), e)
    return list(seen.values())


def nyc_rows():
    out = []
    for m in LOCAL:
        for r in csv.DictReader(open(ROOT / "results/ziel_nyc_v1/event_window" / m / "predictions.csv")):
            out.append((r["model"], r["arm"], r["family"], r["state"], r["year"], int(r["horizon"]),
                        abs(float(r["prediction"]) - float(r["actual"])) / float(r["mase_scale"])))
    return out


def balanced(rows, keep=lambda r: True):
    cell = defaultdict(list)
    for r in rows:
        if keep(r):
            cell[r[:6]].append(r[6])
    # (model, arm, family, state, year, h) -> mean; then state within year, year within family, family
    lvl = defaultdict(list)
    for (mo, a, f, s, y, h), v in cell.items():
        lvl[(mo, a, f, y, h)].append(mean(v))
    fam = defaultdict(list)
    for (mo, a, f, y, h), v in lvl.items():
        fam[(mo, a, f, h)].append(mean(v))
    top = defaultdict(list)
    for (mo, a, f, h), v in fam.items():
        top[(mo, a, h)].append(mean(v))
    return {k: mean(v) for k, v in top.items()}


IR, NR = india_rows(), nyc_rows()
IB, NB = balanced(IR), balanced(NR)


def parse(title):
    block = MS.split(title, 1)[1].split("\n\n", 2)[1]
    lines = [l for l in block.splitlines() if l.startswith("|")]
    head = [c.strip() for c in lines[0].strip("|").split("|")]
    return head, [[c.strip() for c in l.strip("|").split("|")] for l in lines[2:]]


checked = 0
for title, B, h in [("Table A6.", IB, 1), ("Table A8.", NB, 8)]:
    head, body = parse(title)
    for row in body:
        for col, cell in zip(head[1:], row[1:]):
            want = f"{B[(NAMES[row[0]], COL[col], h)]:.5f}"
            checked += 1
            if want != cell:
                problems.append((title, row[0], col, cell, want))


def contrast(B, m, a, b, h):
    return B[(m, a, h)] - B[(m, b, h)]


for title, B, h, split in [("Table A7.", IB, 1, "year"), ("Table A9.", NB, 8, "mode")]:
    rows = IR if B is IB else NR
    head, body = parse(title)
    fams = sorted({r[2] for r in rows})
    groups = sorted({r[4] for r in rows}) if split == "year" else sorted({r[3] for r in rows})
    for row in body:
        m = NAMES[row[0]]; a_name, b_name = [x.strip() for x in row[1].split("−")]
        a, b = SHORT[a_name], SHORT[b_name]
        full = contrast(B, m, a, b, h)
        parts = [contrast(balanced(rows, (lambda g: (lambda r: r[4] == g))(g) if split == "year" else (lambda g: (lambda r: r[3] == g))(g)), m, a, b, h) for g in groups]
        lofo = [contrast(balanced(rows, (lambda x: (lambda r: r[2] != x))(x)), m, a, b, h) for x in fams]
        want = [f"{full:.5f}"] + [f"{p:.5f}" for p in parts] + [f"{min(lofo):.5f} to {max(lofo):.5f}"]
        flips = sum((x > 0) != (full > 0) or x == 0 for x in lofo)
        same = all(p > 0 for p in parts) or all(p < 0 for p in parts)
        label = "negligible" if abs(full) < 0.005 else ("consistent" if same and flips == 0 else "unstable")
        got = row[2:2 + len(want)] + [row[-1]]
        checked += len(want) + 1
        if got != want + [label]:
            problems.append((title, row[0], row[1], got, want + [label]))


# ---------- counts quoted in the text ----------
def count(B, a, b, steps, sign):
    v = [contrast(B, m, a, b, h) for m in LOCAL for h in steps]
    return sum((x < 0) if sign < 0 else (x > 0) for x in v)


IS, NS = (1, 7, 14), (8, 14, 21)
claims = {
    "India each design lower than calendar 12/12": all(count(IB, a, "calendar", IS, -1) == 12 for a in ["sunday_day", "replace_pooled", "replace_typed"]),
    f"NYC hSun raises vs calendar in {count(NB, 'sunday_day', 'calendar', NS, 1)} of 12": f"hSun raises event MASE relative to calendar in {count(NB, 'sunday_day', 'calendar', NS, 1)} of 12" in MS,
    "NYC Rph raises vs calendar": f"Rph in {count(NB, 'replace_pooled', 'calendar', NS, 1)} (" in MS and f"RpH in {count(NB, 'replace_typed', 'calendar', NS, 1)} (" in MS,
    "abstract NYC counts": f"in NYC hSun raises event MASE relative to calendar in {count(NB, 'sunday_day', 'calendar', NS, 1)} of 12 cells" in MS,
    "India Rph lower than pooled": f"Rph is lower than pooled day in {count(IB, 'replace_pooled', 'pooled_day5', IS, -1)} of 12 cells and RpH lower than typed day in {count(IB, 'replace_typed', 'day5', IS, -1)} of 12" in MS,
    "NYC Rph lower than pooled": f"Rph is lower than pooled day in {count(NB, 'replace_pooled', 'pooled_day5', NS, -1)} of 12 cells, while RpH is higher than typed day in {count(NB, 'replace_typed', 'day5', NS, 1)}" in MS,
}
add = {(m, h): contrast(IB, m, "day5", "pooled_day5", h) for m in LOCAL for h in IS}
rep = {(m, h): contrast(IB, m, "replace_typed", "replace_pooled", h) for m in LOCAL for h in IS}
claims["India replacing keeps sign 11/12, SARIMAX lead 7 exception"] = (sum(add[k] * rep[k] > 0 for k in add) == 11
    and [k for k in add if add[k] * rep[k] < 0] == [("sarimax", 7)] and f"only {add[('sarimax', 7)]:.6f}" in MS)
addn = {(m, h): contrast(NB, m, "day5", "pooled_day5", h) for m in LOCAL for h in NS}
repn = {(m, h): contrast(NB, m, "replace_typed", "replace_pooled", h) for m in LOCAL for h in NS}
s, o = sum(addn[k] * repn[k] > 0 for k in addn), sum(addn[k] * repn[k] < 0 for k in addn)
claims["NYC replacing sign counts"] = f"in {s} of 12 NYC cells, the opposite sign in {o} and ties in {12 - s - o}" in MS
cs = sum(rep[(m, h)] * repn[(m, h + 7)] > 0 for m in LOCAL for h in IS)
co = sum(rep[(m, h)] * repn[(m, h + 7)] < 0 for m in LOCAL for h in IS)
claims["India-NYC agreement under replacing"] = f"agree in sign in {cs} of 12 local model/lead cells, are opposite in {co} and tie in {12 - cs - co}" in MS
lg = contrast(IB, "lightgbm", "sunday_day", "pooled_day5", 1)
claims["LightGBM hSun gap"] = f"{-lg:.5f} below pooled day" in MS
for k, v in claims.items():
    checked += 1
    if not v:
        problems.append(("claim", k))


# ---------- labels for any lead, additive flags, ordinary cohorts ----------
def label(rows, B, m, a, b, h, split):
    fams = sorted({r[2] for r in rows})
    groups = sorted({r[4] for r in rows}) if split == "year" else sorted({r[3] for r in rows})
    full = contrast(B, m, a, b, h)
    parts = [contrast(balanced(rows, (lambda g: (lambda r: r[4] == g))(g) if split == "year" else (lambda g: (lambda r: r[3] == g))(g)), m, a, b, h) for g in groups]
    lofo = [contrast(balanced(rows, (lambda x: (lambda r: r[2] != x))(x)), m, a, b, h) for x in fams] if len(fams) > 1 else []
    flips = sum((x > 0) != (full > 0) or x == 0 for x in lofo)
    same = all(p > 0 for p in parts) or all(p < 0 for p in parts)
    return ("negligible" if abs(full) < 0.005 else ("consistent" if same and flips == 0 else "unstable")), parts


def ncons(rows, B, a, b, steps, split):
    return sum(label(rows, B, m, a, b, h, split)[0] == "consistent" for m in LOCAL for h in steps)


def ncons_up(rows, B, a, b, steps):
    return sum(label(rows, B, m, a, b, h, "mode")[0] == "consistent" and contrast(B, m, a, b, h) > 0 for m in LOCAL for h in steps)


def ordinary(folder_runs, steps):
    out = []
    for d in folder_runs:
        for m in LOCAL:
            for r in csv.DictReader(open(ROOT / d / m / "predictions.csv")):
                out.append((r["model"], r["arm"], r["family"], r["state"], r["year"], int(r["horizon"]),
                            abs(float(r["prediction"]) - float(r["actual"])) / float(r["mase_scale"])))
    return balanced(out)


IOB = ordinary(["results/ziel_replacing_v1/ordinary", "results/ziel_replacing_v2/ordinary"], IS)
NOB = ordinary(["results/ziel_nyc_v1/ordinary"], NS)
io = [count(IOB, a, "calendar", IS, -1) for a in ["sunday_day", "replace_pooled", "replace_typed"]]
no = [count(NOB, a, "calendar", NS, -1) for a in ["sunday_day", "replace_pooled", "replace_typed"]]
abc = sum(IB[(m, a, h)] < IB[(m, "calendar", h)] for m in LOCAL for a in ("day5", "pooled_day5") for h in IS)
negs = [(m, h) for m in LOCAL for h in IS if label(IR, IB, m, "sunday_day", "pooled_day5", h, "year")[0] == "negligible"]
negmax = max(max(abs(p) for p in label(IR, IB, m, "sunday_day", "pooled_day5", h, "year")[1]) for m, h in negs)
more = {
    "India consistent vs calendar": f"(consistent in 12, 12 and {ncons(IR, IB, 'replace_typed', 'calendar', IS, 'year')} cells for hSun, Rph and RpH)" in MS
        and ncons(IR, IB, 'sunday_day', 'calendar', IS, 'year') == 12 and ncons(IR, IB, 'replace_pooled', 'calendar', IS, 'year') == 12,
    "additive flags beat calendar": f"also beat calendar in {abc} of their 24 cells" in MS,
    "India consistent vs additive": f"in only {ncons(IR, IB, 'replace_pooled', 'pooled_day5', IS, 'year')} and {ncons(IR, IB, 'replace_typed', 'day5', IS, 'year')} cells" in MS
        and f"in only {ncons(IR, IB, 'replace_pooled', 'pooled_day5', IS, 'year')} (Rph) and {ncons(IR, IB, 'replace_typed', 'day5', IS, 'year')} (RpH) of 12 cells" in MS,
    "negligible count and year spread": f"below 0.005 MASE in {len(negs)} of 12 cells, although single years in those cells differ by up to {negmax:.3f}" in MS,
    "India ordinary": f"lower MASE relative to calendar in {io[0]}, {io[1]} and {io[2]} of 12 cells, so their effect" in MS,
    "NYC ordinary": f"the three designs lower MASE relative to calendar in {no[0]}, {no[1]} and {no[2]} of 12 cells." in MS,
    "NYC consistent rises vs calendar": (f"({ncons_up(NR, NB, 'sunday_day', 'calendar', NS)} of these rises consistent across both modes" in MS
        and f"Rph in {count(NB, 'replace_pooled', 'calendar', NS, 1)} ({ncons_up(NR, NB, 'replace_pooled', 'calendar', NS)} consistent rises)" in MS
        and f"RpH in {count(NB, 'replace_typed', 'calendar', NS, 1)} ({ncons_up(NR, NB, 'replace_typed', 'calendar', NS)} consistent rise)" in MS
        and f"of 12 cells ({ncons_up(NR, NB, 'sunday_day', 'calendar', NS)} of them consistent)" in MS),
}
for k, v in more.items():
    checked += 1
    if not v:
        problems.append(("claim", k))

# ---------- v6 text preserved ----------
v6_paras = [p.strip() for p in V6.split("\n\n") if p.strip()]
v7_text = MS
missing = [p[:80] for p in v6_paras if p not in v7_text and not p.startswith("**Integrated research draft")]
# paragraphs deliberately edited by the builder
edited_starts = ["Sparse events create", "Kreusel et al. [1]", "Eight main arms", "Table 3 gives", "NYC's complete event", "The evidence is conditional", "The named-date correction"]
unexpected = [p for p in missing if not any(p.startswith(s) for s in edited_starts)]
if unexpected:
    problems.append(("v6 paragraphs changed unexpectedly", unexpected))

result = {"checked_items": checked, "problems": problems, "pass": not problems}
json.dump(result, open(ROOT / "manuscript/integrated_review_v7/recomputation_v7_audit.json", "w"), indent=1, default=str)
print(json.dumps(result, indent=1, default=str)[:3000])
sys.exit(0 if not problems else 1)
