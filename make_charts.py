"""Charts for the report: Q2 daily activity, Q4 count vs depth, load-test scaling.  python make_charts.py"""
import csv
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import RESULTS_DIR

CH = RESULTS_DIR / "charts"; CH.mkdir(exist_ok=True)

# ---- Q2: daily count and value (from the PostgreSQL answer)
data = json.loads((RESULTS_DIR / "compare_full_outputs.json").read_text())
q2 = data.get("Q2", {}).get("pg")
if isinstance(q2, list):
    days = [r[0][5:] for r in q2]
    fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    ax[0].bar(days, [r[1] for r in q2]); ax[0].set_ylabel("Transfers per day (count)")
    ax[1].bar(days, [r[2] / 1e9 for r in q2], color="tab:green"); ax[1].set_ylabel("Total value (billion RWF)")
    ax[1].set_xlabel("September 2026 (CAT day, MM-DD)"); plt.setp(ax[1].get_xticklabels(), rotation=90)
    fig.suptitle("Q2 daily activity"); fig.tight_layout(); fig.savefig(CH / "q2_daily.png", dpi=150); plt.close(fig)

# ---- Q4: reached accounts vs depth, one line per review set
fig, ax = plt.subplots(figsize=(8, 5))
for k in "ABCDEF":
    xs, ys = [], []
    for d in (4, 6, 8, 10):
        rows = data.get(f"Q4-{k}-d{d}", {}).get("pg")
        if isinstance(rows, list):
            xs.append(d); ys.append(sum(r[1] for r in rows))
    if xs:
        ax.plot(xs, ys, marker="o", label=f"Set {k}")
ax.set_xlabel("Maximum number of links"); ax.set_ylabel("Distinct accounts reached"); ax.set_xticks([4, 6, 8, 10])
ax.set_title("Q4 reach versus depth"); ax.legend(); fig.tight_layout(); fig.savefig(CH / "q4_depth.png", dpi=150); plt.close(fig)

# ---- Section 7.2: throughput and p95 versus clients
try:
    rows = list(csv.DictReader(open(RESULTS_DIR / "loadtest_summary.csv")))
except FileNotFoundError:
    rows = []
for metric, label in (("throughput_per_s", "Throughput (correct completions / s)"), ("p95_latency_s", "p95 latency (s)")):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, wl in zip(axes, ("q4", "q7")):
        for eng, name in (("pg", "PostgreSQL"), ("neo", "Neo4j")):
            pts = sorted((int(r["clients"]), float(r[metric])) for r in rows if r["workload"] == wl and r["engine"] == eng and r[metric] not in ("", "None"))
            if pts:
                ax.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", label=name)
        ax.set_title({"q4": "Q4 depth 10", "q7": "Q7 length-only bound 6"}[wl]); ax.set_xlabel("Clients"); ax.set_ylabel(label)
        ax.set_xticks([1, 4, 8, 16]); ax.legend()
    fig.tight_layout(); fig.savefig(CH / f"load_{metric}.png", dpi=150); plt.close(fig)
print("Charts written to", CH)
