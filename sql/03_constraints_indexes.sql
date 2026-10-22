-- Section 2.2: foreign keys, indexes, BRIN and ANALYZE. Record the total time separately from loading.
--   psql -U postgres -d mobile_money -f sql/03_constraints_indexes.sql
\set ON_ERROR_STOP on
\timing on

-- Foreign keys: added NOT VALID (instant) then VALIDATE (scans the data once).
ALTER TABLE accounts        ADD CONSTRAINT fk_accounts_customer   FOREIGN KEY (customer_id) REFERENCES customers (customer_id) NOT VALID;
ALTER TABLE account_devices ADD CONSTRAINT fk_ad_account          FOREIGN KEY (account_id)  REFERENCES accounts  (account_id)  NOT VALID;
ALTER TABLE account_devices ADD CONSTRAINT fk_ad_device           FOREIGN KEY (device_id)   REFERENCES devices   (device_id)   NOT VALID;
ALTER TABLE transfers       ADD CONSTRAINT fk_transfers_sender    FOREIGN KEY (sender_id)   REFERENCES accounts  (account_id)  NOT VALID;
ALTER TABLE transfers       ADD CONSTRAINT fk_transfers_receiver  FOREIGN KEY (receiver_id) REFERENCES accounts  (account_id)  NOT VALID;

ALTER TABLE accounts        VALIDATE CONSTRAINT fk_accounts_customer;
ALTER TABLE account_devices VALIDATE CONSTRAINT fk_ad_account;
ALTER TABLE account_devices VALIDATE CONSTRAINT fk_ad_device;
ALTER TABLE transfers       VALIDATE CONSTRAINT fk_transfers_sender;
ALTER TABLE transfers       VALIDATE CONSTRAINT fk_transfers_receiver;

-- Indexes required by the handout.
CREATE INDEX ix_accounts_customer         ON accounts (customer_id, account_id);
CREATE INDEX ix_account_devices_device    ON account_devices (device_id, account_id);
CREATE INDEX ix_transfers_sender_time     ON transfers (sender_id, occurred_at)   INCLUDE (receiver_id, amount_rwf, transfer_id);
CREATE INDEX ix_transfers_receiver_time   ON transfers (receiver_id, occurred_at) INCLUDE (sender_id, amount_rwf, transfer_id);
CREATE INDEX brin_transfers_occurred_at   ON transfers USING brin (occurred_at);

ANALYZE;
\timing off
