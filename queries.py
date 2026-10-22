"""All SQL (psycopg %(name)s) and Cypher ($name) query text for Q1-Q7, built in matched pairs."""
from common import case_params

# ------------------------------------------------------------------ Q1 account activity
Q1_SQL = """
SELECT COUNT(*) AS outgoing_count, COALESCE(SUM(amount_rwf), 0) AS outgoing_rwf
FROM transfers
WHERE sender_id = %(account)s AND occurred_at >= %(start)s AND occurred_at < %(end)s
"""
Q1_CYPHER = """
MATCH (a:Account {account_id: $account})-[t:TRANSFER]->()
WHERE t.occurred_at >= $start AND t.occurred_at < $end
RETURN count(t) AS outgoing_count, coalesce(sum(t.amount_rwf), 0) AS outgoing_rwf
"""

# ------------------------------------------------------------------ Q2 daily activity (CAT days)
Q2_SQL = """
SELECT (to_timestamp(occurred_at) AT TIME ZONE 'Africa/Kigali')::date AS day,
       COUNT(*) AS transfers, SUM(amount_rwf) AS total_rwf
FROM transfers
GROUP BY 1
ORDER BY 1
"""
Q2_CYPHER = """
MATCH ()-[t:TRANSFER]->()
WITH datetime({epochSeconds: t.occurred_at, timezone: 'Africa/Kigali'}) AS ts, t.amount_rwf AS amount
WITH toString(date(ts)) AS day, amount
RETURN day, count(*) AS transfers, sum(amount) AS total_rwf
ORDER BY day
"""

# ------------------------------------------------------------------ Q3 shared devices
Q3_SQL = """
SELECT o.account_id AS other_account, a.device_id, d.access_type,
       GREATEST(a.first_day, o.first_day) AS overlap_start,
       LEAST(a.last_day, o.last_day)      AS overlap_end
FROM account_devices a
JOIN account_devices o ON o.device_id = a.device_id AND o.account_id <> a.account_id
JOIN devices d         ON d.device_id = a.device_id
WHERE a.account_id = %(account)s
  AND GREATEST(a.first_day, o.first_day) <= LEAST(a.last_day, o.last_day)
ORDER BY o.account_id, a.device_id
"""
Q3_CYPHER = """
MATCH (a:Account {account_id: $account})-[ua:USED_DEVICE]->(d:Device)<-[ub:USED_DEVICE]-(b:Account)
WHERE b <> a
WITH b, d,
     CASE WHEN ua.first_day > ub.first_day THEN ua.first_day ELSE ub.first_day END AS s,
     CASE WHEN ua.last_day  < ub.last_day  THEN ua.last_day  ELSE ub.last_day  END AS e
WHERE s <= e
RETURN b.account_id AS other_account, d.device_id AS device_id, d.access_type AS access_type,
       s AS overlap_start, e AS overlap_end
ORDER BY other_account, device_id
"""

# ------------------------------------------------------------------ Q4 ownership + device network
Q4_SQL = """
WITH RECURSIVE edges(sk, si, dk, di) AS (
    SELECT 'Customer', customer_id, 'Account',  account_id  FROM accounts
    UNION ALL SELECT 'Account',  account_id,  'Customer', customer_id FROM accounts
    UNION ALL SELECT 'Account',  account_id,  'Device',   device_id   FROM account_devices
    UNION ALL SELECT 'Device',   device_id,   'Account',  account_id  FROM account_devices
), walk(kind, id, depth) AS (
    SELECT 'Account', %(account)s::integer, 0
    UNION
    SELECT e.dk, e.di, w.depth + 1
    FROM walk w JOIN edges e ON e.sk = w.kind AND e.si = w.id
    WHERE w.depth < %(depth)s
)
SELECT c.region, COUNT(*) AS accounts
FROM (SELECT DISTINCT id FROM walk WHERE kind = 'Account' AND id <> %(account)s) r
JOIN accounts a  ON a.account_id = r.id
JOIN customers c ON c.customer_id = a.customer_id
GROUP BY c.region
ORDER BY c.region
"""
# Cypher cannot take the path bound as a parameter, so __DEPTH__ is replaced by a validated integer.
Q4_CYPHER = """
MATCH (a:Account {account_id: $account})
MATCH (a)-[:OWNS|USED_DEVICE*1..__DEPTH__]-(b:Account)
WHERE b <> a
WITH DISTINCT b
MATCH (c:Customer)-[:OWNS]->(b)
RETURN c.region AS region, count(b) AS accounts
ORDER BY region
"""

# ------------------------------------------------------------------ Q5 rapid onward payments
Q5_SQL = """
SELECT t1.transfer_id AS first_id, t2.transfer_id AS second_id, t3.transfer_id AS third_id,
       t3.receiver_id AS final_receiver
FROM transfers t1
JOIN transfers t2 ON t2.sender_id = t1.receiver_id
                 AND t2.occurred_at > t1.occurred_at AND t2.occurred_at <= t1.occurred_at + 600
JOIN transfers t3 ON t3.sender_id = t2.receiver_id
                 AND t3.occurred_at > t2.occurred_at AND t3.occurred_at <= t2.occurred_at + 600
WHERE t1.sender_id = %(account)s AND t1.occurred_at >= %(start)s AND t1.occurred_at < %(end)s
  AND 90 * t1.amount_rwf::bigint <= 100 * t2.amount_rwf::bigint
  AND 100 * t2.amount_rwf::bigint <= 105 * t1.amount_rwf::bigint
  AND 90 * t2.amount_rwf::bigint <= 100 * t3.amount_rwf::bigint
  AND 100 * t3.amount_rwf::bigint <= 105 * t2.amount_rwf::bigint
  AND t1.receiver_id <> t1.sender_id AND t2.receiver_id <> t1.sender_id AND t3.receiver_id <> t1.sender_id
  AND t2.receiver_id <> t1.receiver_id AND t3.receiver_id <> t1.receiver_id
  AND t3.receiver_id <> t2.receiver_id
ORDER BY t1.transfer_id, t2.transfer_id, t3.transfer_id
"""
Q5_CYPHER = """
MATCH (a1:Account {account_id: $account})-[t1:TRANSFER]->(a2:Account)
      -[t2:TRANSFER]->(a3:Account)-[t3:TRANSFER]->(a4:Account)
WHERE t1.occurred_at >= $start AND t1.occurred_at < $end
  AND t2.occurred_at > t1.occurred_at AND t2.occurred_at <= t1.occurred_at + 600
  AND t3.occurred_at > t2.occurred_at AND t3.occurred_at <= t2.occurred_at + 600
  AND 90 * t1.amount_rwf <= 100 * t2.amount_rwf AND 100 * t2.amount_rwf <= 105 * t1.amount_rwf
  AND 90 * t2.amount_rwf <= 100 * t3.amount_rwf AND 100 * t3.amount_rwf <= 105 * t2.amount_rwf
  AND a1 <> a2 AND a1 <> a3 AND a1 <> a4 AND a2 <> a3 AND a2 <> a4 AND a3 <> a4
RETURN t1.transfer_id AS first_id, t2.transfer_id AS second_id, t3.transfer_id AS third_id,
       a4.account_id AS final_receiver
ORDER BY first_id, second_id, third_id
"""

# ------------------------------------------------------------------ Q6 circular payments
Q6_SQL = """
WITH RECURSIVE walk(cur, ids, first_t, last_t, last_amt, n) AS (
    SELECT t.receiver_id, ARRAY[t.transfer_id], t.occurred_at, t.occurred_at, t.amount_rwf::bigint, 1
    FROM transfers t
    WHERE t.sender_id = %(account)s AND t.occurred_at >= %(start)s AND t.occurred_at < %(end)s
    UNION ALL
    SELECT t.receiver_id, w.ids || t.transfer_id, w.first_t, t.occurred_at, t.amount_rwf::bigint, w.n + 1
    FROM walk w
    JOIN transfers t ON t.sender_id = w.cur
    WHERE w.cur <> %(account)s                              -- stop at the first return
      AND w.n < 8
      AND t.occurred_at > w.last_t AND t.occurred_at < %(end)s
      AND t.occurred_at - w.first_t <= 1800
      AND 90 * w.last_amt <= 100 * t.amount_rwf::bigint
      AND 100 * t.amount_rwf::bigint <= 105 * w.last_amt
)
SELECT ids, n AS length FROM walk
WHERE cur = %(account)s AND n BETWEEN 3 AND 8
ORDER BY ids
"""
Q6_CYPHER = """
MATCH (a:Account {account_id: $account})
MATCH p = (a)-[ts:TRANSFER*3..8]->(a)
WHERE all(r IN ts WHERE r.occurred_at >= $start AND r.occurred_at < $end)
  AND all(n IN nodes(p)[1..-1] WHERE n <> a)
  AND ts[size(ts) - 1].occurred_at - ts[0].occurred_at <= 1800
  AND all(i IN range(0, size(ts) - 2) WHERE
        ts[i].occurred_at < ts[i + 1].occurred_at
        AND 90 * ts[i].amount_rwf <= 100 * ts[i + 1].amount_rwf
        AND 100 * ts[i + 1].amount_rwf <= 105 * ts[i].amount_rwf)
RETURN [r IN ts | r.transfer_id] AS ids, size(ts) AS length
ORDER BY ids
"""

# ------------------------------------------------------------------ Q7 shortest person-only transfer route
# v1 = straightforward recursive BFS (account, depth states de-duplicated by UNION)
Q7_SQL_V1 = """
WITH RECURSIVE walk(id, depth) AS (
    SELECT a.account_id, 0 FROM accounts a WHERE a.account_id = %(source)s AND a.role = 'person'
    UNION
    SELECT t.receiver_id, w.depth + 1
    FROM walk w
    JOIN transfers t ON t.sender_id = w.id
    JOIN accounts a  ON a.account_id = t.receiver_id AND a.role = 'person'
    WHERE w.depth < %(bound)s
)
SELECT MIN(depth) AS length FROM walk WHERE id = %(destination)s
"""
# v2 = improvement attempt: search from BOTH ends (forward ceil(bound/2), backward floor(bound/2)) and meet in the middle
Q7_SQL_V2 = """
WITH RECURSIVE fwd(id, depth) AS (
    SELECT a.account_id, 0 FROM accounts a WHERE a.account_id = %(source)s AND a.role = 'person'
    UNION
    SELECT t.receiver_id, f.depth + 1
    FROM fwd f
    JOIN transfers t ON t.sender_id = f.id
    JOIN accounts a  ON a.account_id = t.receiver_id AND a.role = 'person'
    WHERE f.depth < %(fwd_depth)s
), bwd(id, depth) AS (
    SELECT a.account_id, 0 FROM accounts a WHERE a.account_id = %(destination)s AND a.role = 'person'
    UNION
    SELECT t.sender_id, b.depth + 1
    FROM bwd b
    JOIN transfers t ON t.receiver_id = b.id
    JOIN accounts a  ON a.account_id = t.sender_id AND a.role = 'person'
    WHERE b.depth < %(bwd_depth)s
)
SELECT MIN(f.depth + b.depth) AS length
FROM fwd f JOIN bwd b ON b.id = f.id
WHERE f.depth + b.depth <= %(bound)s
"""
# Path retrieval (not timed): two bounded half-searches that carry arrays, joined at the meeting account.
Q7_SQL_PATH = """
WITH RECURSIVE fwd(id, path, depth) AS (
    SELECT a.account_id, ARRAY[a.account_id], 0 FROM accounts a
    WHERE a.account_id = %(source)s AND a.role = 'person'
    UNION ALL
    SELECT t.receiver_id, f.path || t.receiver_id, f.depth + 1
    FROM fwd f
    JOIN transfers t ON t.sender_id = f.id
    JOIN accounts a  ON a.account_id = t.receiver_id AND a.role = 'person'
    WHERE f.depth < %(fwd_depth)s AND t.receiver_id <> ALL (f.path)
), bwd(id, path, depth) AS (
    SELECT a.account_id, ARRAY[a.account_id], 0 FROM accounts a
    WHERE a.account_id = %(destination)s AND a.role = 'person'
    UNION ALL
    SELECT t.sender_id, t.sender_id || b.path, b.depth + 1
    FROM bwd b
    JOIN transfers t ON t.receiver_id = b.id
    JOIN accounts a  ON a.account_id = t.sender_id AND a.role = 'person'
    WHERE b.depth < %(bwd_depth)s AND t.sender_id <> ALL (b.path)
)
SELECT f.path || b.path[2:] AS path, f.depth + b.depth AS length
FROM fwd f JOIN bwd b ON b.id = f.id
ORDER BY length
LIMIT 1
"""
# Native shortest path; the all(...) predicate lets Neo4j apply the person restriction DURING the search.
Q7_CYPHER_LENGTH = """
MATCH (src:Account {account_id: $source}), (dst:Account {account_id: $destination})
MATCH p = shortestPath((src)-[:TRANSFER*..__BOUND__]->(dst))
WHERE all(n IN nodes(p) WHERE n.role = 'person')
RETURN length(p) AS length
"""
Q7_CYPHER_PATH = """
MATCH (src:Account {account_id: $source}), (dst:Account {account_id: $destination})
MATCH p = shortestPath((src)-[:TRANSFER*..__BOUND__]->(dst))
WHERE all(n IN nodes(p) WHERE n.role = 'person')
RETURN [n IN nodes(p) | n.account_id] AS path, length(p) AS length,
       [r IN relationships(p) | r.transfer_id] AS transfer_ids
"""


def build(qid, engine, case=None, depth=None, bound=None, q7_version="v1", q7_mode="length"):
    """Return (query_text, params) for one logical case. engine is 'pg' or 'neo'."""
    p = case_params(case, depth, bound)
    pg = engine == "pg"
    if qid == "Q1":
        return (Q1_SQL if pg else Q1_CYPHER), p
    if qid == "Q2":
        return (Q2_SQL if pg else Q2_CYPHER), {}
    if qid == "Q3":
        return (Q3_SQL if pg else Q3_CYPHER), p
    if qid == "Q4":
        return (Q4_SQL if pg else Q4_CYPHER.replace("__DEPTH__", str(int(depth)))), p
    if qid == "Q5":
        return (Q5_SQL if pg else Q5_CYPHER), p
    if qid == "Q6":
        return (Q6_SQL if pg else Q6_CYPHER), p
    if qid == "Q7":
        if pg:
            text = Q7_SQL_PATH if q7_mode == "path" else (Q7_SQL_V1 if q7_version == "v1" else Q7_SQL_V2)
        else:
            text = (Q7_CYPHER_PATH if q7_mode == "path" else Q7_CYPHER_LENGTH).replace("__BOUND__", str(int(bound)))
        return text, p
    raise ValueError(qid)


def execute_case(runner, qid, case=None, depth=None, bound=None, q7_version="v1", q7_mode="length"):
    """Build and run one case; return raw rows (not normalised)."""
    text, params = build(qid, runner.engine, case, depth, bound, q7_version, q7_mode)
    rows = runner.run(text, params)
    if qid == "Q7" and q7_mode == "length" and not rows:
        rows = [(None,)]            # Cypher returns no row when no route exists within the bound
    return rows
