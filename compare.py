"""Section 6.1: run all 61 cases on PostgreSQL and Neo4j, normalise, compare exactly.

  python compare.py                    # all 61 cases
  python compare.py --only Q3 Q5       # subset
  python compare.py --q7-version v2    # use the improved SQL for Q7 (Section 6.3)

Cases: Q1 x6, Q2 x1, Q3 x6, Q4 x24 (6 sets x depths 4/6/8/10), Q5 x6, Q6 x6, Q7 x12 (6 sets x bounds 4/6).
Q7 lengths are compared exactly; the supporting paths are checked for validity (they may legitimately differ).
"""
import argparse
import csv
import json
import time

from common import CASE_ORDER, NeoRunner, PgRunner, normalise_rows
from config import RESULTS_DIR
from queries import build, execute_case

TIMEOUT = 900  # seconds, generous: this run checks correctness, not speed


def all_cases():
    cases = [("Q1", k, None, None) for k in CASE_ORDER]
    cases += [("Q2", None, None, None)]
    cases += [("Q3", k, None, None) for k in CASE_ORDER]
    cases += [("Q4", k, d, None) for k in CASE_ORDER for d in (4, 6, 8, 10)]
    cases += [("Q5", k, None, None) for k in CASE_ORDER]
    cases += [("Q6", k, None, None) for k in CASE_ORDER]
    cases += [("Q7", k, None, b) for k in CASE_ORDER for b in (4, 6)]
    return cases


def case_id(q, k, d, b):
    return "-".join(str(x) for x in (q, k, f"d{d}" if d else None, f"b{b}" if b else None) if x)


def verify_path(pg, source, dest, accounts, length, transfer_ids=None):
    """Checks: endpoints, length, every account is a person, every hop is a stored transfer in the right direction."""
    checks = {"endpoints": accounts[0] == source and accounts[-1] == dest, "length": len(accounts) - 1 == length}
    roles = dict(pg.run("SELECT account_id, role FROM accounts WHERE account_id = ANY(%(ids)s)", {"ids": list(accounts)}))
    checks["roles"] = all(roles.get(a) == "person" for a in accounts)
    hops = True
    for u, v in zip(accounts, accounts[1:]):
        hops &= bool(pg.run("SELECT 1 FROM transfers WHERE sender_id = %(u)s AND receiver_id = %(v)s LIMIT 1", {"u": u, "v": v}))
    checks["direction_and_event_exist"] = hops
    if transfer_ids is not None:
        rows = {t: (s, r) for t, s, r in pg.run(
            "SELECT transfer_id, sender_id, receiver_id FROM transfers WHERE transfer_id = ANY(%(ids)s)", {"ids": list(transfer_ids)})}
        checks["transfer_ids_match_hops"] = all(rows.get(t) == (u, v) for t, (u, v) in zip(transfer_ids, zip(accounts, accounts[1:])))
    return checks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="e.g. Q3 Q5")
    ap.add_argument("--q7-version", default="v1", choices=["v1", "v2"])
    args = ap.parse_args()
    pg, neo = PgRunner(), NeoRunner()
    pg.prepare(TIMEOUT); neo.prepare(TIMEOUT)

    cases = [c for c in all_cases() if not args.only or c[0] in args.only]
    print(f"Running {len(cases)} cases (Q7 SQL version {args.q7_version})")
    full, table = {}, []
    for q, k, d, b in cases:
        cid = case_id(q, k, d, b)
        entry = {"case": cid}
        out = {}
        for runner in (pg, neo):
            try:
                t0 = time.perf_counter()
                rows = normalise_rows(execute_case(runner, q, k, d, b, q7_version=args.q7_version))
                entry[f"{runner.engine}_seconds"] = round(time.perf_counter() - t0, 3)
                out[runner.engine] = rows
            except Exception as e:                                   # noqa: BLE001
                out[runner.engine] = f"ERROR: {type(e).__name__}: {str(e)[:200]}"
        entry["pg"], entry["neo"] = out["pg"], out["neo"]
        if isinstance(out["pg"], str) or isinstance(out["neo"], str):
            status = "ERROR"
        else:
            status = "MATCH" if out["pg"] == out["neo"] else "MISMATCH"
        entry["status"] = status

        if q == "Q7":                                                # supporting paths, checked separately
            from common import CASES
            c = CASES[k]
            entry["paths"] = {}
            for runner in (pg, neo):
                try:
                    rows = execute_case(runner, "Q7", k, None, b, q7_mode="path")
                    if not rows:
                        entry["paths"][runner.engine] = "no route within bound"
                    else:
                        path, length = rows[0][0], rows[0][1]
                        tids = rows[0][2] if runner.engine == "neo" else None
                        entry["paths"][runner.engine] = {"path": list(path), "length": length,
                                                         "checks": verify_path(pg, c["account"], c["destination"], list(path), length, tids)}
                except Exception as e:                               # noqa: BLE001
                    entry["paths"][runner.engine] = f"ERROR: {str(e)[:200]}"
        full[cid] = entry
        rows_pg = len(out["pg"]) if isinstance(out["pg"], list) else "-"
        print(f"{cid:14s} {status:9s} pg_rows={rows_pg} pg={entry.get('pg_seconds')}s neo={entry.get('neo_seconds')}s", flush=True)
        table.append({"case": cid, "status": status, "pg_rows": rows_pg,
                      "neo_rows": len(out["neo"]) if isinstance(out["neo"], list) else "-",
                      "pg_seconds": entry.get("pg_seconds"), "neo_seconds": entry.get("neo_seconds")})

    suffix = "" if args.q7_version == "v1" else "_q7v2"
    (RESULTS_DIR / f"compare_full_outputs{suffix}.json").write_text(json.dumps(full, indent=1, default=str))
    with open(RESULTS_DIR / f"compare_status{suffix}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0].keys())); w.writeheader(); w.writerows(table)
    n_ok = sum(t["status"] == "MATCH" for t in table)
    print(f"\n{n_ok}/{len(table)} cases MATCH.  Mismatches/errors:",
          [t["case"] for t in table if t["status"] != "MATCH"] or "none")


if __name__ == "__main__":
    main()
