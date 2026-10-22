"""Section 6.2 / 6.3: time 21 cases per engine (3 untimed warm-ups, 5 measured runs each).

  python benchmark.py                      # all 21 cases, both engines, Q7 SQL v1
  python benchmark.py --q7-version v2      # only the 4 Q7 cases with the improved SQL (Section 6.3)
  python benchmark.py --only Q2 --engine pg
Timeouts: 180 s per warm-up, 60 s per measured run. Errors/timeouts are stored with their status and are
NEVER counted as completed timings. Timer: time.perf_counter() from submission to the last received row.
"""
import argparse
import csv
import statistics
from datetime import datetime
from time import perf_counter

from common import CAT, classify, digest, make_runner, normalise_rows
from config import RESULTS_DIR
from queries import execute_case

WARMUPS, RUNS, WARM_TIMEOUT, RUN_TIMEOUT = 3, 5, 180, 60


def cases21():
    c = [("Q1", k, None, None) for k in "BE"] + [("Q3", k, None, None) for k in "BE"]
    c += [("Q5", k, None, None) for k in "BE"] + [("Q6", k, None, None) for k in "BE"]
    c += [("Q2", None, None, None)]
    c += [("Q4", k, d, None) for k in "BE" for d in (4, 6, 8, 10)]
    c += [("Q7", k, None, b) for k in "BE" for b in (4, 6)]
    return c


def cid(q, k, d, b):
    return "-".join(str(x) for x in (q, k, f"d{d}" if d else None, f"b{b}" if b else None) if x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", nargs="*", default=["pg", "neo"], choices=["pg", "neo"])
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--q7-version", default="v1", choices=["v1", "v2"])
    ap.add_argument("--fast-fail", action="store_true", help="skip measured runs if every warm-up failed")
    args = ap.parse_args()

    cases = [c for c in cases21() if not args.only or c[0] in args.only]
    if args.q7_version == "v2":
        cases = [c for c in cases if c[0] == "Q7"]
    tag = "" if args.q7_version == "v1" else "_q7v2"
    runs_path = RESULTS_DIR / f"benchmark_runs{tag}.csv"
    fields = ["case", "engine", "run_type", "run_no", "start_cat", "seconds", "rows", "status", "answer_digest", "params"]
    new = not runs_path.exists()
    fh = open(runs_path, "a", newline=""); w = csv.DictWriter(fh, fieldnames=fields)
    if new:
        w.writeheader()

    last_digest = {}
    for engine in args.engine:
        runner = make_runner(engine)                       # one persistent connection per engine
        for q, k, d, b in cases:
            case = cid(q, k, d, b)
            params = f"case={k} depth={d} bound={b} q7={args.q7_version if q == 'Q7' else '-'}"
            print(f"\n[{engine}] {case}", flush=True)
            ok_warm = 0
            for i in range(1, WARMUPS + 1):                # --- untimed warm-ups
                runner.prepare(WARM_TIMEOUT)
                start = datetime.now(CAT).isoformat(timespec="seconds"); t0 = perf_counter()
                try:
                    execute_case(runner, q, k, d, b, q7_version=args.q7_version); status = "ok"; ok_warm += 1
                except Exception as e:                      # noqa: BLE001
                    status = classify(e)
                w.writerow(dict(case=case, engine=engine, run_type="warmup", run_no=i, start_cat=start,
                                seconds=round(perf_counter() - t0, 4), rows="", status=status, answer_digest="", params=params))
                fh.flush()
                if status != "ok" and args.fast_fail:
                    break
            if args.fast_fail and ok_warm == 0:
                print("  all warm-ups failed -> skipping measured runs"); continue
            durations = []
            for i in range(1, RUNS + 1):                    # --- measured runs
                runner.prepare(RUN_TIMEOUT)                 # outside the timed region
                start = datetime.now(CAT).isoformat(timespec="seconds")
                t0 = perf_counter()
                try:
                    rows = execute_case(runner, q, k, d, b, q7_version=args.q7_version)
                    secs = perf_counter() - t0              # stop immediately after the final row arrived
                    status, n = "ok", len(rows)
                    last_digest[(case, engine)] = digest(normalise_rows(rows))   # compared outside the timer
                    durations.append(secs)
                except Exception as e:                      # noqa: BLE001
                    secs = perf_counter() - t0; status = classify(e); n = ""
                w.writerow(dict(case=case, engine=engine, run_type="measured", run_no=i, start_cat=start,
                                seconds=round(secs, 4), rows=n, status=status,
                                answer_digest=last_digest.get((case, engine), ""), params=params))
                fh.flush()
                print(f"  run {i}: {secs * 1000:10.1f} ms  {status}", flush=True)
            if durations:
                print(f"  median {statistics.median(durations) * 1000:.1f} ms over {len(durations)} completed runs")
        runner.close()
    fh.close()
    summarise(runs_path, tag)


def summarise(runs_path, tag):
    rows = list(csv.DictReader(open(runs_path)))
    stats = {}
    for r in rows:
        key = (r["case"], r["engine"])
        s = stats.setdefault(key, {"ms": [], "bad": 0, "digest": set()})
        if r["run_type"] != "measured":
            continue
        if r["status"] == "ok":
            s["ms"].append(float(r["seconds"]) * 1000); s["digest"].add(r["answer_digest"])
        else:
            s["bad"] += 1
    out = []
    for case in sorted({c for c, _ in stats}):
        row = {"case": case}
        for eng in ("pg", "neo"):
            s = stats.get((case, eng))
            if s and s["ms"]:
                row.update({f"{eng}_median_ms": round(statistics.median(s["ms"]), 1), f"{eng}_min_ms": round(min(s["ms"]), 1),
                            f"{eng}_max_ms": round(max(s["ms"]), 1), f"{eng}_errors_timeouts": s["bad"]})
            else:
                row.update({f"{eng}_median_ms": "", f"{eng}_min_ms": "", f"{eng}_max_ms": "",
                            f"{eng}_errors_timeouts": s["bad"] if s else "n/a"})
        pm, nm = row.get("pg_median_ms"), row.get("neo_median_ms")
        row["pg_over_neo_median_ratio"] = round(pm / nm, 2) if pm and nm else ""
        dp, dn = stats.get((case, "pg"), {}).get("digest"), stats.get((case, "neo"), {}).get("digest")
        row["answers_agree"] = (dp == dn) if dp and dn else ""
        out.append(row)
    path = RESULTS_DIR / f"benchmark_summary{tag}.csv"
    if out:
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    print(f"\n{'case':12s} {'pg med ms':>11s} {'neo med ms':>11s} {'pg/neo':>8s}  err/timeouts(pg,neo)")
    for r in out:
        print(f"{r['case']:12s} {str(r['pg_median_ms']):>11s} {str(r['neo_median_ms']):>11s} "
              f"{str(r['pg_over_neo_median_ratio']):>8s}  ({r['pg_errors_timeouts']},{r['neo_errors_timeouts']})")
    print("Saved", path)


if __name__ == "__main__":
    main()
