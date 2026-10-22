"""Section 1.2: capture the five generator streams into CSV files.

Run:  python capture.py
Writes data/<stream>.csv progressively (never holds a stream in memory) and
results/capture_audit.json with counts, seconds, sizes and transfer audit totals.
"""
import csv
import json
import os
import time
from itertools import islice

import mobile_money_generator as g
from config import DATA_DIR, RESULTS_DIR

STREAMS = {
    "customers": g.iter_customers,
    "accounts": g.iter_accounts,
    "devices": g.iter_devices,
    "account_devices": g.iter_account_devices,
    "transfers": g.iter_transfers,
}


def preview():
    info = g.dataset_info()
    print("Dataset period :", info["period"], "| currency:", info["currency"])
    print("Expected counts:", info["expected_counts"])
    print("FIELDS         :", g.FIELDS)
    for name, factory in STREAMS.items():
        print(f"\n--- {name}: first 10 records ---")
        for row in islice(factory(), 10):   # fresh iterator each time
            print(row)


def capture():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    expected = g.dataset_info()["expected_counts"]
    results = {}
    audit = {"transfer_count": 0, "min_occurred_at": None, "max_occurred_at": None, "sum_amount_rwf": 0}

    for name, factory in STREAMS.items():
        path = DATA_DIR / f"{name}.csv"
        consumed = written = 0
        t0 = time.perf_counter()
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=g.FIELDS[name])
            writer.writeheader()
            for row in factory():
                consumed += 1
                writer.writerow(row)
                written += 1
                if name == "transfers":
                    audit["transfer_count"] += 1
                    t = row["occurred_at"]
                    if audit["min_occurred_at"] is None or t < audit["min_occurred_at"]:
                        audit["min_occurred_at"] = t
                    if audit["max_occurred_at"] is None or t > audit["max_occurred_at"]:
                        audit["max_occurred_at"] = t
                    audit["sum_amount_rwf"] += row["amount_rwf"]
                    if consumed % 1_000_000 == 0:
                        print(f"  transfers: {consumed:,} rows after {time.perf_counter() - t0:,.0f}s", flush=True)
        seconds = time.perf_counter() - t0
        size = os.path.getsize(path)
        results[name] = {
            "consumed": consumed, "written": written, "expected": expected[name],
            "count_matches": written == expected[name],
            "capture_seconds": round(seconds, 2), "csv_bytes": size, "csv_gb": round(size / 1e9, 4),
        }
        print(f"{name:16s} consumed={consumed:>11,} written={written:>11,} expected={expected[name]:>11,} "
              f"match={written == expected[name]} seconds={seconds:8.1f} size={size / 1e9:.3f} GB", flush=True)

    total = sum(r["written"] for r in results.values())
    print(f"\nTotal source records: {total:,} (handout says 20,993,500)")
    print("Transfer audit:", audit)
    with open(RESULTS_DIR / "capture_audit.json", "w") as f:
        json.dump({"results": results, "transfer_audit": audit, "total_records": total}, f, indent=2)


if __name__ == "__main__":
    preview()
    print("\n===== FULL CAPTURE =====")
    capture()
