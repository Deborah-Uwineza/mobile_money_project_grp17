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

## Setup (Windows)

Keep the project **outside OneDrive** (about 10 GB of CSVs and stores), e.g. `C:\BDA\mobile_money_project`.

```bat
cd /d C:\BDA\mobile_money_project
python -m pip install --default-timeout=200 --retries 10 -r requirements.txt

set MM_PG_DSN=host=localhost port=5432 dbname=mobile_money user=postgres password=YOUR_PASSWORD
set MM_NEO4J_PASSWORD=YOUR_PASSWORD
set NEO4J_HOME=C:\path\to\neo4j-community-x.y.z
set PGPASSWORD=YOUR_PASSWORD
```
Never commit real passwords; `config.py` only contains `CHANGE_ME` placeholders.

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

## Submit

```bat
python make_submission_zip.py      :: creates ..\mobile_money_submission.zip (no CSVs, no database stores)
git init
git add .
git commit -m "Project 2: mobile money investigations"
git remote add origin https://github.com/Deborah-Uwineza/<repository-name>.git
git push -u origin main
```
`data/` and `import_tmp/` are git-ignored. Keep `results/` (raw timings, comparison outputs, plans) in the submission.
