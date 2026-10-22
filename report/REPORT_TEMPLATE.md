# Project 2 Report: Mobile Money Investigations with PostgreSQL and Neo4j

Group members and student IDs: ______  (up to 3)
Submit as ONE PDF in milestone order. Keep explanations brief; reference earlier screenshots for repeated evidence.
Every screenshot: executed command, result, taskbar and clock visible.

## 1 Capture the data
- 1.1 Workspace [2]: screenshots of both connections, versions, CPU/RAM/OS, DB memory settings, PostgreSQL timezone `Africa/Kigali`.
- 1.2 capture.py [5]: ten-record preview of each stream; five-stream totals with seconds, CSV sizes, transfer audit.

## 2 PostgreSQL
- 2.1 Tables [4]: schema drawing (`docs/schema.md`), field meanings and units, screenshot of definitions and constraints.
- 2.2 Load and checks [5]: loading seconds, index/constraint seconds, counts, roles (240,000 / 6,000 / 2,000), audit match, validated constraints, indexes, data and index sizes (1 GB = 1,000,000,000 bytes).

## 3 Neo4j
- 3.1 Graph mapping [4]: graph schema drawing, every source field mapped (`docs/schema.md`).
- 3.2 Import [5]: `prepare_import.py`, full import command and completion, constraints, indexes ONLINE, import/setup seconds, store and transaction-log GB, verification (704,600 nodes; 20,536,900 relationships), temporary copies removed.
- 3.3 One account in both models [3]: matching records; write: how foreign keys become relationships; what time/event evidence is lost if repeated payments collapse into one edge.

## 4 Routine questions (all six sets A to F)
- Q1 [3]: six paired results; explain why outgoing value is not a balance.
- Q2 [3]: 30 days, reconciliation with the capture totals, charts with units; one pattern; why transfer value is not provider revenue.
- Q3 [4]: results/counts for all sets; one legitimate sharing scenario; why overlap is not simultaneous use.

## 5 Connected accounts
- Q4 [6]: 24 comparisons, predictions for depths 8 and 10 written BEFORE running them, count-versus-depth plot, one supporting path, how deeper links add weak associations.
- Q5 [5]: six counts, one chain (IDs, CAT times, amounts), why this does not prove the same funds moved.
- Q6 [5]: six counts, one cycle, further evidence you would request.
- Q7 [6]: 12 length comparisons and path checks, why no route within four transfers is not "no connection", why a structural route is not onward movement of funds.

## 6 Correctness and performance
- 6.1 [4]: 61-case status table; mismatches resolved; independent Python check of one device overlap and one chain/cycle.
- 6.2 [5]: 21 cases per engine (3 warm-ups, 5 runs), median/min/max ms and ratio, EXPLAIN/PROFILE for Q2, Q4 B depth 10, Q7 B bound 6, one processing difference.
- 6.3 [5]: plan evidence of wasted search, prediction, before/after correctness, timings and plans, selected version and why (an honest unsuccessful attempt can earn full marks).

## 7 Concurrency
- 7.1 [5]: active clients, all 16 combination summaries (throughput, median, p95, errors, timeouts).
- 7.2 [4]: throughput and p95 plots, 1 versus 16 clients, resource/plan evidence, does a graph advantage survive the SQL improvement (limit claims to this experiment).

## 8 Decisions
- 8.1 [5] Priority table for A/D, B/E, C/F using Q3 to Q7; one pair in detail (IDs, amounts, times, device evidence); one chain/cycle diagram and one ownership-device diagram from YOUR results; an ordinary explanation, missing evidence. Do not declare fraud.
- 8.2 [5] Recommendation (max 500 words): reporting, traversal, concurrency, load time/storage; one SQL/Cypher/plan comparison; evidence against your preferred choice; modelling benefit vs implementation effect; freshness target and stale-data consequence; two limits.
- 8.3 [3] Individual judgement: each member writes 150 to 200 named words on a DIFFERENT measured finding, its explanation and a check that could overturn it. List contributions and any LLM/external assistance and how it was checked.

## 9 Submission
- GitHub URL: ______   ZIP: mobile_money_submission.zip
- Screenshots: generator unchanged (`verify_generator.py`), rerun of the 61-case comparison, both database services stopped.

### Member notes (write these yourselves)
**Member 1 (name):**  _150 to 200 words_

**Member 2 (name):**  _150 to 200 words_

**Member 3 (name):**  _150 to 200 words_

### Contributions and assistance disclosure
_Who did what. State that an AI assistant helped produce the starter code package, and how each member checked it (what they ran, what they compared, what they changed)._
