"""Section 7.1: concurrent load test with multiprocessing, one persistent connection per process and a Barrier.

  python loadtest.py --q7-version v1      # use the SQL version you selected in Section 6
  python loadtest.py --engine pg --workload q4 --clients 1 4
Workloads: q4 = Q4 depth 10 ; q7 = Q7 length-only bound 6. Each client cycles A-B-C, 15 s window, 60 s query timeout,
clients 1/4/8/16, 3 repetitions per engine/workload/client-count.
"""
import argparse
import csv
import math
import multiprocessing as mp
import statistics
import time
from time import perf_counter

from common import classify, digest, make_runner, normalise_rows
from config import RESULTS_DIR
from queries import execute_case

CYCLE = ("A", "B", "C")
WINDOW, TIMEOUT, REPS = 15.0, 60, 3
CLIENTS = (1, 4, 8, 16)
WORKLOADS = {"q4": dict(qid="Q4", depth=10, bound=None), "q7": dict(qid="Q7", depth=None, bound=6)}


def one_request(runner, wl, case, q7v):
    return normalise_rows(execute_case(runner, wl["qid"], case, wl["depth"], wl["bound"], q7_version=q7v))


def worker(idx, engine, wl_name, q7v, barrier, start_v, deadline_v, out_q):
    wl = WORKLOADS[wl_name]
    runner = make_runner(engine)                       # persistent connection for this process
    runner.prepare(TIMEOUT)
    for case in CYCLE:                                 # warm-up A-B-C once
        try:
            one_request(runner, wl, case, q7v)
        except Exception:                              # noqa: BLE001
            pass
    barrier.wait(timeout=900)
    while start_v.value == 0.0:                        # wait for the common start time set at barrier release
        time.sleep(0.0005)
    deadline = deadline_v.value
    log, cycle = [], 0
    while time.time() < deadline:                      # start cycles until the deadline, finish a started cycle
        for case in CYCLE:
            t_wall, t0 = time.time(), perf_counter()
            try:
                rows = one_request(runner, wl, case, q7v); status, dg = "ok", digest(rows)
            except Exception as e:                     # noqa: BLE001
                status, dg = classify(e), ""
            log.append((idx, cycle, case, t_wall, perf_counter() - t0, status, dg))
        cycle += 1
    out_q.put((idx, log, time.time()))
    runner.close()


def reference(wl_name, q7v):
    """Expected digests per case, from both engines (they must agree)."""
    wl, ref = WORKLOADS[wl_name], {}
    for engine in ("pg", "neo"):
        r = make_runner(engine); r.prepare(900)
        for case in CYCLE:
            ref.setdefault(case, set()).add(digest(one_request(r, wl, case, q7v)))
        r.close()
    bad = [c for c, s in ref.items() if len(s) != 1]
    if bad:
        raise SystemExit(f"Engines disagree on {wl_name} cases {bad}; fix correctness (compare.py) before load testing.")
    return {c: next(iter(s)) for c, s in ref.items()}


def run_once(engine, wl_name, n, q7v, expected):
    ctx = mp.get_context("spawn")
    barrier = ctx.Barrier(n + 1)                       # n clients + this coordinator
    start_v, deadline_v, out_q = ctx.Value("d", 0.0), ctx.Value("d", 0.0), ctx.Queue()
    procs = [ctx.Process(target=worker, args=(i, engine, wl_name, q7v, barrier, start_v, deadline_v, out_q)) for i in range(n)]
    for p in procs:
        p.start()
    print(f"   active clients: {n}  pids: {[p.pid for p in procs]}", flush=True)
    barrier.wait(timeout=900)
    start = time.time()
    deadline_v.value = start + WINDOW
    start_v.value = start                              # releases the workers
    results = [out_q.get(timeout=WINDOW + TIMEOUT + 300) for _ in procs]
    for p in procs:
        p.join()
    finish = max(r[2] for r in results)
    log = [row for r in results for row in r[1]]
    good = [r for r in log if r[5] == "ok" and r[6] == expected[r[2]]]
    lat = sorted(r[4] for r in good)
    p95 = lat[math.ceil(0.95 * len(lat)) - 1] if lat else None
    summary = dict(engine=engine, workload=wl_name, clients=n,
                   throughput_per_s=round(len(good) / (finish - start), 4),
                   median_latency_s=round(statistics.median(lat), 4) if lat else None,
                   p95_latency_s=round(p95, 4) if p95 is not None else None,
                   correct=len(good), errors=sum(r[5] == "error" or (r[5] == "ok" and r[6] != expected[r[2]]) for r in log),
                   timeouts=sum(r[5] == "timeout" for r in log), elapsed_s=round(finish - start, 3))
    return summary, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", nargs="*", default=["pg", "neo"], choices=["pg", "neo"])
    ap.add_argument("--workload", nargs="*", default=["q4", "q7"], choices=["q4", "q7"])
    ap.add_argument("--clients", nargs="*", type=int, default=list(CLIENTS))
    ap.add_argument("--q7-version", default="v1", choices=["v1", "v2"])
    args = ap.parse_args()

    rep_rows, req_rows = [], []
    for wl in args.workload:
        expected = reference(wl, args.q7_version)
        for engine in args.engine:
            for n in args.clients:
                for rep in range(1, REPS + 1):
                    print(f"[{engine}] {wl} clients={n} repetition={rep}", flush=True)
                    s, log = run_once(engine, wl, n, args.q7_version, expected)
                    s["repetition"] = rep
                    rep_rows.append(s)
                    req_rows += [dict(engine=engine, workload=wl, clients=n, repetition=rep, client=r[0], cycle=r[1], case=r[2],
                                      start_epoch=round(r[3], 4), seconds=round(r[4], 4), status=r[5],
                                      correct=(r[5] == "ok" and r[6] == expected[r[2]])) for r in log]
                    print("  ", {k: s[k] for k in ("throughput_per_s", "median_latency_s", "p95_latency_s", "errors", "timeouts")}, flush=True)
    for name, rows in (("loadtest_repetitions.csv", rep_rows), ("loadtest_requests.csv", req_rows)):
        if rows:
            with open(RESULTS_DIR / name, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    summary = []
    for key in sorted({(r["workload"], r["engine"], r["clients"]) for r in rep_rows}):
        reps = [r for r in rep_rows if (r["workload"], r["engine"], r["clients"]) == key]
        med = lambda f: (statistics.median([r[f] for r in reps if r[f] is not None]) if any(r[f] is not None for r in reps) else None)
        summary.append(dict(workload=key[0], engine=key[1], clients=key[2], throughput_per_s=med("throughput_per_s"),
                            median_latency_s=med("median_latency_s"), p95_latency_s=med("p95_latency_s"),
                            errors=med("errors"), timeouts=med("timeouts")))
    if summary:
        with open(RESULTS_DIR / "loadtest_summary.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(summary[0].keys())); w.writeheader(); w.writerows(summary)
        print("\nSUMMARY (median of repetitions)")
        for s in summary:
            print(s)


if __name__ == "__main__":
    mp.freeze_support()
    main()
