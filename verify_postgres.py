"""Section 2.2: compare PostgreSQL with capture_audit.json; print counts, roles, constraints, indexes, sizes."""
import json

from common import PgRunner
from config import RESULTS_DIR

audit = json.load(open(RESULTS_DIR / "capture_audit.json"))
pg = PgRunner()
ok = True


def check(label, got, want):
    global ok
    good = got == want
    ok &= good
    print(f"[{'OK' if good else 'FAIL'}] {label}: got {got:,} want {want:,}" if isinstance(got, int)
          else f"[{'OK' if good else 'FAIL'}] {label}: got {got} want {want}")


for table, info in audit["results"].items():
    check(f"count({table})", pg.run(f"SELECT COUNT(*) FROM {table}")[0][0], info["expected"])

roles = dict(pg.run("SELECT role, COUNT(*) FROM accounts GROUP BY role"))
check("person accounts", roles.get("person"), 240_000)
check("merchant accounts", roles.get("merchant"), 6_000)
check("agent accounts", roles.get("agent"), 2_000)

n, lo, hi, total = pg.run("SELECT COUNT(*), MIN(occurred_at), MAX(occurred_at), SUM(amount_rwf::bigint) FROM transfers")[0]
a = audit["transfer_audit"]
check("transfer count", n, a["transfer_count"])
check("earliest occurred_at", lo, a["min_occurred_at"])
check("latest occurred_at", hi, a["max_occurred_at"])
check("sum amount_rwf", int(total), a["sum_amount_rwf"])

print("\nConstraints (convalidated must be True):")
for r in pg.run("SELECT conrelid::regclass::text, conname, contype, convalidated FROM pg_constraint "
                "WHERE connamespace = 'public'::regnamespace ORDER BY 1, 2"):
    print(" ", r)
print("\nIndexes:")
for r in pg.run("SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY 1, 2"):
    print(" ", r)
print("\nSizes (1 GB = 1,000,000,000 bytes):")
print("  database GB:", round(pg.run("SELECT pg_database_size(current_database())")[0][0] / 1e9, 3))
for name, t, i in pg.run("SELECT relname, pg_table_size(c.oid), pg_indexes_size(c.oid) FROM pg_class c "
                         "WHERE relnamespace = 'public'::regnamespace AND relkind = 'r' ORDER BY 1"):
    print(f"  {name:16s} table {t / 1e9:7.3f} GB   indexes {i / 1e9:7.3f} GB")
print("\nALL CHECKS PASSED" if ok else "\nSOME CHECKS FAILED")
