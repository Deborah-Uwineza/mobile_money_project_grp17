// Section 3.2 step 3 (setup_neo4j.py runs these and times them)
CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.customer_id IS UNIQUE;
CREATE CONSTRAINT account_id_unique  IF NOT EXISTS FOR (a:Account)  REQUIRE a.account_id  IS UNIQUE;
CREATE CONSTRAINT device_id_unique   IF NOT EXISTS FOR (d:Device)   REQUIRE d.device_id   IS UNIQUE;
CREATE RANGE INDEX transfer_occurred_at IF NOT EXISTS FOR ()-[t:TRANSFER]-() ON (t.occurred_at);
CALL db.awaitIndexes(3600);
SHOW CONSTRAINTS;
SHOW INDEXES;
