-- Section 2.2: quick psql checks for screenshots (verify_postgres.py also compares with capture_audit.json).
SELECT 'customers' AS tbl, COUNT(*) FROM customers
UNION ALL SELECT 'accounts', COUNT(*) FROM accounts
UNION ALL SELECT 'devices', COUNT(*) FROM devices
UNION ALL SELECT 'account_devices', COUNT(*) FROM account_devices
UNION ALL SELECT 'transfers', COUNT(*) FROM transfers;

SELECT role, COUNT(*) FROM accounts GROUP BY role ORDER BY role;

SELECT COUNT(*) AS transfer_count, MIN(occurred_at) AS min_occurred_at,
       MAX(occurred_at) AS max_occurred_at, SUM(amount_rwf::bigint) AS sum_amount_rwf
FROM transfers;

SELECT conrelid::regclass AS tbl, conname, contype, convalidated
FROM pg_constraint WHERE connamespace = 'public'::regnamespace AND contype IN ('p', 'f', 'c')
ORDER BY 1, 2;

SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' ORDER BY 1, 2;

SELECT ROUND(pg_database_size(current_database()) / 1e9, 3) AS database_gb;
SELECT relname,
       ROUND(pg_table_size(c.oid) / 1e9, 3)   AS table_gb,
       ROUND(pg_indexes_size(c.oid) / 1e9, 3) AS index_gb
FROM pg_class c WHERE relnamespace = 'public'::regnamespace AND relkind = 'r' ORDER BY relname;
