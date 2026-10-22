-- Section 2.1: five PostgreSQL tables. Run from the project root:
--   psql -U postgres -d mobile_money -f sql/01_schema.sql
-- Foreign keys are added in 03_constraints_indexes.sql AFTER the bulk load,
-- so that "loading seconds" and "index/constraint setup seconds" can be recorded separately.
\set ON_ERROR_STOP on
SET timezone TO 'Africa/Kigali';
ALTER DATABASE mobile_money SET timezone TO 'Africa/Kigali';

DROP TABLE IF EXISTS transfers, account_devices, accounts, devices, customers CASCADE;

CREATE TABLE customers (
    customer_id  INTEGER NOT NULL,
    region       TEXT    NOT NULL,
    CONSTRAINT pk_customers PRIMARY KEY (customer_id)
);

CREATE TABLE accounts (
    account_id   INTEGER NOT NULL,
    customer_id  INTEGER NOT NULL,
    role         TEXT    NOT NULL,
    CONSTRAINT pk_accounts PRIMARY KEY (account_id),
    CONSTRAINT ck_accounts_role CHECK (role IN ('person', 'merchant', 'agent'))
);

CREATE TABLE devices (
    device_id    INTEGER NOT NULL,
    access_type  TEXT    NOT NULL,
    CONSTRAINT pk_devices PRIMARY KEY (device_id),
    CONSTRAINT ck_devices_access CHECK (access_type IN ('handset', 'public_terminal'))
);

CREATE TABLE account_devices (
    account_id    INTEGER  NOT NULL,
    device_id     INTEGER  NOT NULL,
    first_day     SMALLINT NOT NULL,   -- inclusive day number 0..29 (0 = 1 Sep 2026 CAT)
    last_day      SMALLINT NOT NULL,   -- inclusive day number 0..29
    observations  INTEGER  NOT NULL,   -- count of observations inside the interval
    CONSTRAINT pk_account_devices PRIMARY KEY (account_id, device_id),
    CONSTRAINT ck_ad_observations CHECK (observations > 0),
    CONSTRAINT ck_ad_days CHECK (0 <= first_day AND first_day <= last_day AND last_day <= 29)
);

CREATE TABLE transfers (
    transfer_id  BIGINT  NOT NULL,
    sender_id    INTEGER NOT NULL,
    receiver_id  INTEGER NOT NULL,
    occurred_at  BIGINT  NOT NULL,     -- Unix time, seconds
    amount_rwf   INTEGER NOT NULL,     -- positive whole Rwandan francs
    CONSTRAINT pk_transfers PRIMARY KEY (transfer_id),
    CONSTRAINT ck_transfers_amount CHECK (amount_rwf > 0)
);

SHOW timezone;
\d+ customers
\d+ accounts
\d+ devices
\d+ account_devices
\d+ transfers
