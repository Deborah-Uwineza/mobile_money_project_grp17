# Values to cross-check your databases against

These were produced by an independent Python reference run on CSVs captured with the supplied generator
(numpy 2.4.4). Use them as a sanity check only. **Your own capture_audit.json and your database answers are
the evidence you submit.** If your numpy version produced different CSVs, trust your own capture and re-derive
these with `independent_checks.py`.

| Item | Value |
|---|---|
| Source records | 20,993,500 |
| Transfer count | 20,003,300 |
| Earliest occurred_at | 1788235200 |
| Latest occurred_at | 1790798399 |
| Sum of amount_rwf | 231,482,327,870 |

| Set | Q1 count, RWF in hour | Q3 overlaps | Q5 chains | Q6 cycles | Q7 length bound 4 / bound 6 |
|---|---|---|---|---|---|
| A | 1, 200,000 | 4 | 1 | 1 (length 4) | 3 / 3 |
| B | 1, 1,050,000 | 9 | 1 | 0 | none / 5 |
| C | 1, 300,000 | 9 | 1 | 1 (length 6) | none / 5 |
| D | 1, 45,000 | 4 | 0 | 0 | 3 / 3 |
| E | 1, 40,000 | 9 | 0 | 0 | none / 5 |
| F | 1, 30,000 | 9 | 0 | 0 | none / 5 |

Q2 must return 30 CAT days whose counts sum to 20,003,300 and whose values sum to the audit total.
Q4, the 24 depth counts, and all timings must come from your own runs.
