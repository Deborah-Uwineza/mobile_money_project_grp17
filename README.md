# Project 2: Mobile Money Investigations with PostgreSQL and Neo4j

Code for the AUCA MSDA 9215 / Advanced Big Data Analytics Project 2 (issued 12 Oct 2026, due 26 Oct 2026 11:59 PM CAT).
It captures the supplied generator into CSVs, builds the same data in PostgreSQL and Neo4j, answers Q1 to Q7 in both,
checks that the answers match, times them, load-tests them, and produces the charts for the report.

> **Status.** The capture, CSV preparation and the independent Python reference checks were run on the real generator output.
> The SQL and Cypher have **not** been executed against real PostgreSQL / Neo4j servers by the author of this package.
> Run every step yourself, read the output, fix anything your versions reject, and keep your own screenshots.
> Each group member must be able to explain every query (Section 8.3).

## Folder map

| Path | Purpose | Section |
|---|---|---|
| `mobile_money_generator.py`, `generator.sha256`, `verify_generator.py` | Supplied generator (unchanged) and a hash check | 1, 9.2 |
| `config.py` | Paths, connection settings (env vars, placeholder secrets) | all |
| `record_environment.py` | Versions, CPU, RAM, DB memory settings | 1.1 |
| `capture.py` | Stream the 5 generators to CSV, audit totals | 1.2 |
| `sql/01_schema.sql` ... `04_checks.sql` | PostgreSQL tables, load, FKs/indexes, checks | 2 |
| `verify_postgres.py` | Compare PostgreSQL with `capture_audit.json` | 2.2 |
| `prepare_import.py`, `neo4j/import_full.*`, `setup_neo4j.py`, `verify_neo4j.py` | Neo4j import, constraints, checks | 3 |
| `inspect_account.py` | One account traced in both models | 3.3 |
| `queries.py`, `common.py` | All SQL/Cypher pairs Q1 to Q7, runners, helpers | 4, 5 |
| `compare.py`, `independent_checks.py` | 61-case correctness comparison, independent Python checks | 6.1 |
| `benchmark.py`, `explain_plans.py` | 21-case timing, EXPLAIN/PROFILE, SQL improvement | 6.2, 6.3 |
| `loadtest.py`, `make_charts.py` | Concurrent clients, charts | 7 |
| `docs/schema.md` | Both schemas (Mermaid) and field mapping | 2.1, 3.1 |
| `docs/EXPECTED_VALUES.md` | Reference values to sanity-check your results | all |
| `report/REPORT_TEMPLATE.md` | Report skeleton and screenshot checklist | 8, 9 |

## How to run it (Windows, step by step)

Use **one Command Prompt window** for everything: the `set` variables disappear when you close it.
Stop at the first error, copy the full message and fix it before continuing.
Take screenshots (command, result, taskbar and clock visible) as you go.

**Keep the project outside OneDrive** (about 10 GB of CSVs and stores), for example `C:\BDA\mobile_money_project`.
If it must stay in OneDrive, pause syncing while you work, because OneDrive can lock files during loads.

### Phase 0: Setup

```bat
cd /d C:\BDA\mobile_money_project
python verify_generator.py                     :: must say "generator UNCHANGED"
python -m pip install --default-timeout=200 --retries 10 "psycopg[binary]"
python -m pip install --default-timeout=200 --retries 10 neo4j
python -m pip install --default-timeout=200 --retries 10 matplotlib
```
`numpy` is the only package `capture.py` needs. Install the others one at a time if your connection is slow.

<<<<<<< HEAD
### Phase 1: Capture (no database needed)

```bat
python capture.py
```
Final counts must be: customers 228,000, accounts 248,000, devices 228,600, account_devices 285,600,
transfers 20,003,300 (total 20,993,500). Files go to `data\`, the audit to `results\capture_audit.json`.

### Phase 2: PostgreSQL

1. Check `psql --version`. If it is not recognised: `set PATH=%PATH%;C:\Program Files\PostgreSQL\16\bin`.
2. Set the password for this window (avoid `&`, `%`, `^`) and test it:
```bat
set PGPASSWORD=YOUR_PASSWORD
set MM_PG_DSN=host=localhost port=5432 dbname=mobile_money user=postgres password=YOUR_PASSWORD
psql -U postgres -c "SELECT 1"
```
3. Build and load (run from the project root, the load uses relative `data/` paths):
```bat
psql -U postgres -c "CREATE DATABASE mobile_money"
psql -U postgres -d mobile_money -f sql/01_schema.sql
psql -U postgres -d mobile_money -f sql/02_load.sql
psql -U postgres -d mobile_money -f sql/03_constraints_indexes.sql
psql -U postgres -d mobile_money -f sql/04_checks.sql
python verify_postgres.py
```
Write down the `\timing` totals: step `02` = loading seconds, step `03` = index/constraint seconds.
`verify_postgres.py` must end with **ALL CHECKS PASSED**.

**Troubleshooting: "password authentication failed for user postgres".** The password is the one chosen when
PostgreSQL was installed. To reset it: open `C:\Program Files\PostgreSQL\16\data\pg_hba.conf` as administrator,
change `scram-sha-256` to `trust` on the `127.0.0.1/32` and `::1/128` lines, restart the service
(`net stop postgresql-x64-16` then `net start postgresql-x64-16` in an administrator prompt), run
`psql -U postgres -c "ALTER USER postgres PASSWORD 'NewSimplePass'"`, then **change `trust` back to
`scram-sha-256`** and restart the service again.

### Phase 3: Neo4j (Community 5.x, needs Java 17)

```bat
set NEO4J_HOME=C:\path\to\neo4j-community-x.y.z
set MM_NEO4J_PASSWORD=YOUR_NEO4J_PASSWORD
python prepare_import.py                       :: typed-header copies in import_tmp\
neo4j\import_full.bat                          :: Neo4j must be STOPPED
```
Start Neo4j in a **second** window and leave it open: `"%NEO4J_HOME%\bin\neo4j.bat" console`.
First start only: open http://localhost:7474 and change the default `neo4j` / `neo4j` password.
Back in the first window:
```bat
python setup_neo4j.py                          :: constraints + range index, waits until ONLINE
python verify_neo4j.py                         :: 704,600 nodes, 20,536,900 relationships
python prepare_import.py --cleanup             :: remove the temporary import copies
python inspect_account.py 998                  :: one account traced in both models
python record_environment.py                   :: versions, CPU, RAM, memory settings
```

### Phase 4: The questions (both databases loaded)

Start small, then run everything:
```bat
python compare.py --only Q1 Q3
python compare.py --only Q5 Q6
python compare.py --only Q7
python compare.py --only Q2
python compare.py --only Q4
python compare.py                              :: all 61 cases, every one should say MATCH
python independent_checks.py overlap B --compare
python independent_checks.py chain B --compare
python independent_checks.py cycle B --compare
```
Compare your answers with `docs/EXPECTED_VALUES.md`.

### Phase 5: Performance and scaling

Keep only one database service active while timing it (Section 6.2).
```bat
python benchmark.py                            :: 21 cases per engine, 3 warm-ups + 5 runs (can take hours)
python explain_plans.py                        :: EXPLAIN (ANALYZE, BUFFERS) and PROFILE
python benchmark.py --q7-version v2            :: Section 6.3 improvement, 4 Q7 cases
python compare.py --only Q7 --q7-version v2
python explain_plans.py --q7-version v2
python loadtest.py --q7-version v1             :: or v2, whichever you selected
python make_charts.py                          :: charts in results\charts\
```
Use `--only` and `--engine pg|neo` to run pieces. Timeouts are recorded as timeouts, never as timings.

### Phase 6: Final checks

```bat
python verify_generator.py
python compare.py                              :: rerun the 61 cases and screenshot completion
```
Then stop both database services and screenshot the stopped status.

## Notes

* Cypher cannot take a path bound as a parameter, so `queries.py` inserts the validated integer into the text.
* The import scripts use Neo4j 5 syntax (`neo4j-admin database import full`). Older 4.x versions differ.
* If `dbms.components()` or `SHOW SETTINGS` is not allowed, read the memory settings from `conf/neo4j.conf`.
* Neo4j Q4 at depth 10 and Q2 can time out. That is a valid result: record it.

=======
## Run order

Run everything from the project root. Take screenshots (terminal, taskbar and clock visible) at each step.

| # | Command | Handout section |
|---|---|---|
| 1 | `python verify_generator.py` | 1, 9.2 |
| 2 | Create DBs: `psql -U postgres -c "CREATE DATABASE mobile_money"`; install and start Neo4j Community (default `neo4j` database) | 1.1 |
| 3 | `python record_environment.py` (also screenshot `SHOW timezone;` in psql) | 1.1 |
| 4 | `python capture.py` (about 2 to 5 minutes; creates `data/*.csv` and `results/capture_audit.json`) | 1.2 |
| 5 | `psql -U postgres -d mobile_money -f sql/01_schema.sql` | 2.1 |
| 6 | `psql -U postgres -d mobile_money -f sql/02_load.sql` (note the `\timing` totals = loading seconds) | 2.2 |
| 7 | `psql -U postgres -d mobile_money -f sql/03_constraints_indexes.sql` (total = index/constraint seconds) | 2.2 |
| 8 | `psql -U postgres -d mobile_money -f sql/04_checks.sql` then `python verify_postgres.py` | 2.2 |
| 9 | `python prepare_import.py` | 3.2 |
| 10 | Stop Neo4j (`neo4j stop` or the service), then `neo4j\import_full.bat`, then start Neo4j | 3.2 |
| 11 | `python setup_neo4j.py` (constraints, range index, wait until ONLINE) | 3.2 |
| 12 | `python verify_neo4j.py`, then `python prepare_import.py --cleanup` | 3.2 |
| 13 | `python inspect_account.py 998` | 3.3 |
| 14 | `python compare.py` (all 61 cases; start with `--only Q1 Q3` to debug) | 4, 5, 6.1 |
| 15 | `python independent_checks.py overlap B --compare`, `chain B --compare`, `cycle B --compare` | 6.1 |
| 16 | `python benchmark.py` then `python explain_plans.py` (Q2, Q4 B depth 10, Q7 B bound 6) | 6.2 |
| 17 | `python benchmark.py --q7-version v2`, `python compare.py --only Q7 --q7-version v2`, `python explain_plans.py --q7-version v2` | 6.3 |
| 18 | `python loadtest.py --q7-version v1` (or `v2`, whichever you select) | 7.1 |
| 19 | `python make_charts.py` | 5.1, 7.2 |
| 20 | Finally: `python verify_generator.py`, rerun `python compare.py`, stop both DB services, screenshot the stopped status | 9.2 |

Notes:
* Start the slow jobs first: capture (step 4) and the PostgreSQL load (step 6) can run while you read the queries.
* Do not run benchmarks while another heavy job is running, and keep one database service active at a time for timing (Section 6.2). Stop the other service before `benchmark.py --engine pg` or `--engine neo`.
* `benchmark.py` can take hours if Cypher Q4 depth 10 or Q2 time out. Use `--only` and `--engine` to run pieces. Timeouts are recorded as such, never as timings.
* Cypher cannot take a path bound as a parameter, so `queries.py` inserts the validated integer into the text.
* The import scripts use the Neo4j 5 syntax (`neo4j-admin database import full`). Older 4.x versions use a different command.
* If Neo4j reports that `dbms.components()` or `SHOW SETTINGS` is not allowed, read the memory settings from `conf/neo4j.conf`.


>>>>>>> ca839aa20e167c0f23b2971ae87f8d276f3550fd
