"""Section 3.3: trace one loaded account to its owner, a device and an outgoing transfer in both models.
Run: python inspect_account.py [account_id]   (default 998)"""
import sys

from common import NeoRunner, PgRunner

account = int(sys.argv[1]) if len(sys.argv) > 1 else 998

SQL = """
SELECT c.customer_id, c.region, a.account_id, a.role, ad.device_id, d.access_type,
       ad.first_day, ad.last_day, ad.observations, t.transfer_id, t.receiver_id, t.occurred_at, t.amount_rwf
FROM accounts a
JOIN customers c        ON c.customer_id = a.customer_id
JOIN account_devices ad ON ad.account_id = a.account_id
JOIN devices d          ON d.device_id = ad.device_id
JOIN transfers t        ON t.sender_id = a.account_id
WHERE a.account_id = %(account)s
ORDER BY t.occurred_at, t.transfer_id
LIMIT 5
"""
CYPHER = """
MATCH (c:Customer)-[:OWNS]->(a:Account {account_id: $account})-[u:USED_DEVICE]->(d:Device)
MATCH (a)-[t:TRANSFER]->(r:Account)
RETURN c.customer_id, c.region, a.account_id, a.role, d.device_id, d.access_type,
       u.first_day, u.last_day, u.observations, t.transfer_id, r.account_id, t.occurred_at, t.amount_rwf
ORDER BY t.occurred_at, t.transfer_id
LIMIT 5
"""
cols = ["customer_id", "region", "account_id", "role", "device_id", "access_type", "first_day",
        "last_day", "observations", "transfer_id", "receiver_id", "occurred_at", "amount_rwf"]
for label, runner, q in (("PostgreSQL (JOINs)", PgRunner(), SQL), ("Neo4j (MATCH)", NeoRunner(), CYPHER)):
    print(f"\n=== {label} ===")
    print(" | ".join(cols))
    for row in runner.run(q, {"account": account}):
        print(" | ".join(str(v) for v in row))
