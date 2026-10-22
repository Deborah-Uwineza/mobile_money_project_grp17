"""Section 6.1 step 2: independent Python checks against the captured CSV rows (no database involved).

  python independent_checks.py overlap B      # Q3 device overlaps for review account of set B
  python independent_checks.py chain B        # Q5 rapid onward chains
  python independent_checks.py cycle B        # Q6 circular sequences
  python independent_checks.py q1 B           # Q1 outgoing count / value
Add --compare to also run the SQL query on PostgreSQL and print whether the answers agree.
"""
import csv
import sys

from common import CASES, case_params, normalise_rows
from config import DATA_DIR


_CACHE = {}


def window_rows(lo, hi):
    """All transfers with lo <= occurred_at < hi, grouped by sender (streams the 780 MB file once, then cached)."""
    if (lo, hi) in _CACHE:
        return _CACHE[(lo, hi)]
    by_sender = {}
    with open(DATA_DIR / "transfers.csv", newline="") as f:
        rd = csv.reader(f); next(rd)
        for tid, s, r, t, a in rd:
            t = int(t)
            if lo <= t < hi:
                by_sender.setdefault(int(s), []).append((t, int(tid), int(r), int(a)))
    _CACHE[(lo, hi)] = by_sender
    return by_sender


def amount_ok(prev, nxt):
    return 90 * prev <= 100 * nxt <= 105 * prev


def q1(account, start, end):
    n = total = 0
    with open(DATA_DIR / "transfers.csv", newline="") as f:
        rd = csv.reader(f); next(rd)
        for tid, s, r, t, a in rd:
            if int(s) == account and start <= int(t) < end:
                n += 1; total += int(a)
    return [(n, total)]


def overlaps(account):
    rows = list(csv.DictReader(open(DATA_DIR / "account_devices.csv")))
    mine = {int(r["device_id"]): (int(r["first_day"]), int(r["last_day"])) for r in rows if int(r["account_id"]) == account}
    kinds = {int(r["device_id"]): r["access_type"] for r in csv.DictReader(open(DATA_DIR / "devices.csv"))}
    out = []
    for r in rows:
        a, d = int(r["account_id"]), int(r["device_id"])
        if a != account and d in mine:
            s, e = max(mine[d][0], int(r["first_day"])), min(mine[d][1], int(r["last_day"]))
            if s <= e:
                out.append((a, d, kinds[d], s, e))
    return sorted(out)


def chains(account, start, end):
    g = window_rows(start, end + 1200)
    out = []
    for t1, id1, a2, m1 in g.get(account, []):
        if not start <= t1 < end or a2 == account:
            continue
        for t2, id2, a3, m2 in g.get(a2, []):
            if not (t1 < t2 <= t1 + 600 and amount_ok(m1, m2)) or a3 in (account, a2):
                continue
            for t3, id3, a4, m3 in g.get(a3, []):
                if t2 < t3 <= t2 + 600 and amount_ok(m2, m3) and a4 not in (account, a2, a3):
                    out.append((id1, id2, id3, a4))
    return sorted(out)


def cycles(account, start, end):
    g = window_rows(start, end)
    out = []

    def dfs(cur, ids, first_t, last_t, last_amt):
        for t, tid, nxt, amt in g.get(cur, []):
            if t > last_t and t - first_t <= 1800 and amount_ok(last_amt, amt):
                new_ids = ids + [tid]
                if nxt == account:                       # first return: stop here
                    if 3 <= len(new_ids) <= 8:
                        out.append((tuple(new_ids), len(new_ids)))
                elif len(new_ids) < 8:
                    dfs(nxt, new_ids, first_t, t, amt)
    for t, tid, nxt, amt in g.get(account, []):
        if nxt != account:
            dfs(nxt, [tid], t, t, amt)
    return sorted(out)


if __name__ == "__main__":
    what, case = sys.argv[1], sys.argv[2]
    p = case_params(case); acct = p["account"]
    result = {"overlap": lambda: overlaps(acct), "chain": lambda: chains(acct, p["start"], p["end"]),
              "cycle": lambda: cycles(acct, p["start"], p["end"]), "q1": lambda: q1(acct, p["start"], p["end"])}[what]()
    print(f"{what} for set {case} (account {acct}): {len(result)} result(s)")
    for r in result[:20]:
        print(" ", r)
    if "--compare" in sys.argv:
        from common import PgRunner
        from queries import execute_case
        qid = {"overlap": "Q3", "chain": "Q5", "cycle": "Q6", "q1": "Q1"}[what]
        pg = normalise_rows(execute_case(PgRunner(), qid, case))
        print("PostgreSQL agrees with Python:", pg == normalise_rows(result))
