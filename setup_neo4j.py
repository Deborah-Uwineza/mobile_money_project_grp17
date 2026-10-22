"""Section 3.2 step 3: unique constraints on the three business IDs and a range index on TRANSFER.occurred_at."""
import time

from neo4j import GraphDatabase

from config import NEO4J_DB, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER

STATEMENTS = [
    "CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.customer_id IS UNIQUE",
    "CREATE CONSTRAINT account_id_unique IF NOT EXISTS FOR (a:Account) REQUIRE a.account_id IS UNIQUE",
    "CREATE CONSTRAINT device_id_unique IF NOT EXISTS FOR (d:Device) REQUIRE d.device_id IS UNIQUE",
    "CREATE RANGE INDEX transfer_occurred_at IF NOT EXISTS FOR ()-[t:TRANSFER]-() ON (t.occurred_at)",
]

with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver, \
        driver.session(database=NEO4J_DB) as s:
    t0 = time.perf_counter()
    for stmt in STATEMENTS:
        s.run(stmt).consume()
        print("OK:", stmt)
    s.run("CALL db.awaitIndexes(3600)").consume()
    print(f"\nConstraint/index setup seconds: {time.perf_counter() - t0:.1f}")
    print("\nCONSTRAINTS")
    for r in s.run("SHOW CONSTRAINTS YIELD name, type, entityType, labelsOrTypes, properties"):
        print(" ", r.values())
    print("\nINDEXES (state must be ONLINE)")
    for r in s.run("SHOW INDEXES YIELD name, type, entityType, labelsOrTypes, properties, state"):
        print(" ", r.values())
