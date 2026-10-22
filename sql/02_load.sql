-- Section 2.2: bulk load. Run from the PROJECT ROOT so the relative data/ paths resolve:
--   psql -U postgres -d mobile_money -f sql/02_load.sql
-- \timing prints the elapsed milliseconds after every \copy (record the total as "loading seconds").
\set ON_ERROR_STOP on
\timing on
\copy customers       FROM 'data/customers.csv'       CSV HEADER
\copy devices         FROM 'data/devices.csv'         CSV HEADER
\copy accounts        FROM 'data/accounts.csv'        CSV HEADER
\copy account_devices FROM 'data/account_devices.csv' CSV HEADER
\copy transfers       FROM 'data/transfers.csv'       CSV HEADER
\timing off
