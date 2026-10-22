"""Section 1.1: record software versions, hardware and database memory settings -> results/environment.json."""
import json
import os
import platform
import sys
from importlib import metadata

from config import RESULTS_DIR
from common import NeoRunner, PgRunner


def ram_gb():
    try:
        if os.name == "nt":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong), ("total", ctypes.c_ulonglong),
                            ("a", ctypes.c_ulonglong), ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong),
                            ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong), ("e", ctypes.c_ulonglong)]
            m = MS(); m.l = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return round(m.total / 2**30, 1)
        with open("/proc/meminfo") as f:
            return round(int(f.readline().split()[1]) / 2**20, 1)
    except Exception as e:                       # noqa: BLE001
        return f"unknown ({e})"


env = {"python": sys.version, "os": platform.platform(), "cpu": platform.processor(),
       "cpu_threads": os.cpu_count(), "ram_gb": ram_gb(), "packages": {}}
for pkg in ("psycopg", "psycopg-binary", "neo4j", "numpy", "matplotlib"):
    try:
        env["packages"][pkg] = metadata.version(pkg)
    except Exception:                            # noqa: BLE001
        env["packages"][pkg] = "not installed"

try:
    pg = PgRunner()
    env["postgres_version"] = pg.run("SELECT version()")[0][0]
    env["postgres_settings"] = {k: pg.run(f"SHOW {k}")[0][0] for k in (
        "timezone", "shared_buffers", "work_mem", "maintenance_work_mem", "effective_cache_size",
        "max_parallel_workers_per_gather", "max_wal_size", "random_page_cost")}
except Exception as e:                           # noqa: BLE001
    env["postgres_error"] = str(e)
try:
    neo = NeoRunner()
    env["neo4j_components"] = [list(r) for r in neo.run("CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition")]
    try:
        env["neo4j_memory_settings"] = [list(r) for r in neo.run(
            "SHOW SETTINGS YIELD name, value WHERE name STARTS WITH 'server.memory' RETURN name, value")]
    except Exception as e:                       # noqa: BLE001
        env["neo4j_memory_settings"] = f"read server.memory.* from conf/neo4j.conf ({e})"
except Exception as e:                           # noqa: BLE001
    env["neo4j_error"] = str(e)

print(json.dumps(env, indent=2, default=str))
(RESULTS_DIR / "environment.json").write_text(json.dumps(env, indent=2, default=str))
