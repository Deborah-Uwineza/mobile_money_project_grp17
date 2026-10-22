"""Section 3.2 step 4: verify the Neo4j import against capture_audit.json."""
import json
import os
from pathlib import Path

from common import NeoRunner
from config import NEO4J_HOME, RESULTS_DIR

audit = json.load(open(RESULTS_DIR / "capture_audit.json"))
exp = {k: v["expected"] for k, v in audit["results"].items()}
neo = NeoRunner()
ok = True


def check(label, got, want):
    global ok
    good = got == want
    ok &= good
    print(f"[{'OK' if good else 'FAIL'}] {label}: got {got} want {want}")


def one(q):
    return neo.run(q)[0]


check("Customer nodes", one("MATCH (n:Customer) RETURN count(n)")[0], exp["customers"])
check("Account nodes", one("MATCH (n:Account) RETURN count(n)")[0], exp["accounts"])
check("Device nodes", one("MATCH (n:Device) RETURN count(n)")[0], exp["devices"])
check("total nodes", one("MATCH (n) RETURN count(n)")[0], 704_600)
check("OWNS", one("MATCH ()-[r:OWNS]->() RETURN count(r)")[0], exp["accounts"])
check("USED_DEVICE", one("MATCH ()-[r:USED_DEVICE]->() RETURN count(r)")[0], exp["account_devices"])
check("TRANSFER", one("MATCH ()-[r:TRANSFER]->() RETURN count(r)")[0], exp["transfers"])
check("total relationships", one("MATCH ()-[r]->() RETURN count(r)")[0], 20_536_900)

roles = dict(neo.run("MATCH (a:Account) RETURN a.role, count(a)"))
check("person accounts", roles.get("person"), 240_000)
check("merchant accounts", roles.get("merchant"), 6_000)
check("agent accounts", roles.get("agent"), 2_000)
check("accounts without exactly one owner",
      one("MATCH (a:Account) OPTIONAL MATCH (a)<-[o:OWNS]-(:Customer) WITH a, count(o) AS c WHERE c <> 1 RETURN count(a)")[0], 0)

n, distinct, lo, hi, total = one("MATCH ()-[t:TRANSFER]->() RETURN count(t), count(DISTINCT t.transfer_id), "
                                 "min(t.occurred_at), max(t.occurred_at), sum(t.amount_rwf)")
a = audit["transfer_audit"]
check("distinct transfer_id", distinct, n)
check("transfer count (audit)", n, a["transfer_count"])
check("earliest occurred_at", lo, a["min_occurred_at"])
check("latest occurred_at", hi, a["max_occurred_at"])
check("sum amount_rwf", total, a["sum_amount_rwf"])

if NEO4J_HOME:
    def size_gb(path):
        return sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file()) / 1e9
    for label, sub in (("store", "data/databases/neo4j"), ("transaction logs", "data/transactions/neo4j")):
        p = Path(NEO4J_HOME) / sub
        print(f"{label} size: {size_gb(p):.3f} GB ({p})" if p.exists() else f"{label}: {p} not found")
else:
    print("Set NEO4J_HOME to print store / transaction-log sizes in GB.")
print("\nALL CHECKS PASSED" if ok else "\nSOME CHECKS FAILED")
