"""Section 3.2: make temporary Neo4j import copies with typed headers (source CSVs stay unchanged).

Run:  python prepare_import.py            -> creates import_tmp/*.csv
      python prepare_import.py --cleanup  -> removes import_tmp/ after the import has been verified
"""
import csv
import shutil
import sys
import time

from config import DATA_DIR, IMPORT_DIR

HEADERS = {
    "customers":       "customer_id:ID(Customer),region:string",
    "accounts":        "account_id:ID(Account),:IGNORE,role:string",        # customer_id column ignored here
    "devices":         "device_id:ID(Device),access_type:string",
    "account_devices": ":START_ID(Account),:END_ID(Device),first_day:int,last_day:int,observations:int",
    "transfers":       "transfer_id:long,:START_ID(Account),:END_ID(Account),occurred_at:long,amount_rwf:int",
}


def copy_with_header(name, header):
    src, dst = DATA_DIR / f"{name}.csv", IMPORT_DIR / f"{name}.csv"
    t0 = time.perf_counter()
    with open(src, "rb") as fi, open(dst, "wb") as fo:
        fi.readline()                                   # drop the original header line
        fo.write(header.encode() + b"\r\n")
        shutil.copyfileobj(fi, fo, 1 << 20)             # stream the rest, never loading it in memory
    print(f"{name:16s} -> {dst}  ({dst.stat().st_size / 1e9:.3f} GB, {time.perf_counter() - t0:.1f}s)")


def derive_owns():
    """OWNS relationships (Customer -> Account) sorted by customer_id, account_id."""
    pairs = []
    with open(DATA_DIR / "accounts.csv", newline="") as f:
        for row in csv.DictReader(f):
            pairs.append((int(row["customer_id"]), int(row["account_id"])))
    pairs.sort()
    dst = IMPORT_DIR / "owns.csv"
    with open(dst, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([":START_ID(Customer)", ":END_ID(Account)"])
        w.writerows(pairs)
    print(f"{'owns':16s} -> {dst}  ({len(pairs):,} rows)")


def main():
    if "--cleanup" in sys.argv:
        shutil.rmtree(IMPORT_DIR, ignore_errors=True)
        print("Removed", IMPORT_DIR)
        return
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    for name, header in HEADERS.items():
        copy_with_header(name, header)
    derive_owns()


if __name__ == "__main__":
    main()
