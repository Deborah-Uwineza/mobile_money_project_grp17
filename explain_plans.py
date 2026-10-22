"""Section 6.2 / 6.3: collect EXPLAIN (ANALYZE, BUFFERS) and PROFILE outside the timing runs.

  python explain_plans.py              # Q2, Q4 B depth 10, Q7 B bound 6 (v1)
  python explain_plans.py --q7-version v2
Plans are printed and saved to results/plans_<tag>.txt
"""
import argparse

from common import NeoRunner, PgRunner
from config import RESULTS_DIR
from queries import build

ap = argparse.ArgumentParser()
ap.add_argument("--q7-version", default="v1", choices=["v1", "v2"])
args = ap.parse_args()
PLANS = [("Q2", None, None, None), ("Q4", "B", 10, None), ("Q7", "B", None, 6)]
out = []


def neo_profile(runner, text, params):
    from neo4j import Query
    res = runner.session.run(Query("PROFILE " + text, timeout=900), params)
    list(res)
    plan = res.consume().profile
    lines = []

    def walk(p, depth=0):
        a = p.get("args", {})
        lines.append("  " * depth + f"{p['operator_type']}  rows={a.get('Rows')} dbHits={a.get('DbHits')} "
                     f"time(ms)={a.get('Time')} {a.get('Details', '')}")
        for c in p.get("children", []):
            walk(c, depth + 1)
    walk(plan)
    return "\n".join(lines)


pg, neo = PgRunner(), NeoRunner()
pg.prepare(900)
for q, k, d, b in PLANS:
    name = f"{q}-{k}-d{d}" if d else (f"{q}-{k}-b{b}" if b else q)
    text, params = build(q, "pg", k, d, b, q7_version=args.q7_version)
    block = f"\n===== PostgreSQL EXPLAIN (ANALYZE, BUFFERS): {name} =====\n"
    block += "\n".join(r[0] for r in pg.run("EXPLAIN (ANALYZE, BUFFERS) " + text, params))
    text, params = build(q, "neo", k, d, b)
    block += f"\n\n===== Neo4j PROFILE: {name} =====\n" + neo_profile(neo, text, params)
    print(block)
    out.append(block)
(RESULTS_DIR / f"plans_{'q7' + args.q7_version}.txt").write_text("\n".join(out))
