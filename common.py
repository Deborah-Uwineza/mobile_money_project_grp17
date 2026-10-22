"""Shared helpers: review cases, CAT time windows, database runners, result normalisation."""
import hashlib
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from config import NEO4J_DB, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER, PG_DSN

CAT = timezone(timedelta(hours=2), "CAT")          # Africa/Kigali has no daylight saving time
CASES = {                                            # handout table in Section 4
    "A": dict(account=998,    destination=24755,  day=6),
    "B": dict(account=147228, destination=186823, day=13),
    "C": dict(account=206978, destination=6573,   day=8),
    "D": dict(account=237998, destination=21755,  day=6),
    "E": dict(account=144228, destination=183823, day=13),
    "F": dict(account=203978, destination=3573,   day=8),
}
CASE_ORDER = "ABCDEF"


def hour_window(day):
    """09:45:00 inclusive to 10:45:00 exclusive CAT on 2026-09-<day>, as epoch seconds."""
    start = datetime(2026, 9, day, 9, 45, 0, tzinfo=CAT)
    end = datetime(2026, 9, day, 10, 45, 0, tzinfo=CAT)
    return int(start.timestamp()), int(end.timestamp())


def case_params(case, depth=None, bound=None):
    p = {}
    if case is not None:
        c = CASES[case]
        start, end = hour_window(c["day"])
        p.update(account=c["account"], source=c["account"], destination=c["destination"], start=start, end=end)
    if depth is not None:
        p["depth"] = int(depth)
    if bound is not None:
        p.update(bound=int(bound), fwd_depth=(int(bound) + 1) // 2, bwd_depth=int(bound) // 2)
    return p


def classify(exc):
    s = (type(exc).__name__ + " " + str(exc)).lower()
    if any(k in s for k in ("timeout", "timed out", "canceling statement", "querycanceled", "terminated")):
        return "timeout"
    return "error"


# ---------------------------------------------------------------- runners
class PgRunner:
    """One persistent PostgreSQL connection (autocommit)."""
    engine = "pg"

    def __init__(self):
        import psycopg
        self.conn = psycopg.connect(PG_DSN, autocommit=True)
        self._timeout = None

    def prepare(self, timeout_s):
        """Set statement_timeout. Call OUTSIDE the timed region."""
        if timeout_s != self._timeout:
            with self.conn.cursor() as cur:
                cur.execute(f"SET statement_timeout = {int(timeout_s * 1000) if timeout_s else 0}")
            self._timeout = timeout_s

    def run(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params or {})
            return [tuple(r) for r in cur.fetchall()] if cur.description else []

    def close(self):
        self.conn.close()


class NeoRunner:
    """One persistent Neo4j driver + session on the default 'neo4j' database."""
    engine = "neo"

    def __init__(self):
        from neo4j import GraphDatabase
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.session = self.driver.session(database=NEO4J_DB)
        self._timeout = None

    def prepare(self, timeout_s):
        self._timeout = timeout_s

    def run(self, query, params=None):
        from neo4j import Query
        q = Query(query, timeout=self._timeout) if self._timeout else query
        result = self.session.run(q, params or {})
        return [tuple(r.values()) for r in result]

    def close(self):
        self.session.close()
        self.driver.close()


def make_runner(engine):
    return PgRunner() if engine == "pg" else NeoRunner()


_GLOBAL = {}


def run_pg(query, params=None):
    """Required helper: run a PostgreSQL query on a shared persistent connection, return every row."""
    if "pg" not in _GLOBAL:
        _GLOBAL["pg"] = PgRunner()
    return _GLOBAL["pg"].run(query, params)


def run_neo(query, params=None):
    """Required helper: run a Cypher query on a shared persistent session, return every row."""
    if "neo" not in _GLOBAL:
        _GLOBAL["neo"] = NeoRunner()
    return _GLOBAL["neo"].run(query, params)


# ---------------------------------------------------------------- normalisation
def _norm(v):
    if isinstance(v, bool) or v is None:
        return v
    if isinstance(v, int):
        return int(v)
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    if isinstance(v, float):
        return int(v) if v.is_integer() else v
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, (list, tuple)):
        return tuple(_norm(x) for x in v)
    return v


def normalise_rows(rows):
    """Integers as int, dates as ISO text, lists as tuples, then sorted for exact comparison."""
    return sorted((tuple(_norm(x) for x in r) for r in rows), key=repr)


def digest(rows):
    return hashlib.sha256(repr(rows).encode()).hexdigest()[:16]
