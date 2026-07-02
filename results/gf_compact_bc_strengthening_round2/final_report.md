# GF Compact-BC Strengthening Round 2 Final Report

Commit SHA: recorded in the final Codex response. The exact SHA cannot be
embedded in this same committed file without changing the SHA again.

## Answers

1. Single-thread high_imbalance_seed3202 reproduced: yes. The audited one-thread
   compact-BC row certified objective/LB/UB `1.74931345205`.
2. moderate_seed3301 certified: no. It remains noncertified with LB `0.04648`,
   UB `0.0491525526647`, gap about `0.05437`.
3. Dynamic root separation added cuts: yes, on the interval smoke row. It added
   six dynamic visit-inventory-linking cuts from root LP values. V20 focused
   rows did not close from dynamic cuts.
4. Useful cut families: static compact-BC cuts remain useful; dynamic
   visit-inventory-linking is active but not yet decisive on V20 low-Gini leaves.
5. Receiver-source-cover: singleton is paper-safe. Pair/set receiver-cover
   remains diagnostic only pending proof/tests.
6. no_new_cuts/top-level aggregation: summary audit passes; relaxation-only
   certified rows use `none` aggregation rather than misleading enabled-family
   counts.
7. V20 certified count: 2/6 under the audited one-thread round-two mini-suite:
   `high_imbalance_seed3202` and `tight_T_seed3101`.
8. V50/V100 diagnostics: all have final JSON. V50 rows hit `std_bad_alloc`;
   V100 compact rows hit native process exit `-1073741819` and were
   wrapper-finalized as noncertified `model_size_limit`.
9. Compact-BC vs single-thread CPLEX: compact-BC certifies the two V20 rows
   above; one-thread plain CPLEX certifies no V20 row at 300s.
10. Paper-readiness: not ready for broad benchmark claims. The one-thread
    recovery of high_imbalance_seed3202 is important, but moderate_seed3301 and
    several V20 rows remain open, and large-V compact model generation is still
    diagnostic.

## Audit

All required audits passed:

- `certificate_audit.csv`: 43 rows, 0 failures.
- `summary_cleanup_audit.csv`: 43 rows, 0 failures.
- `thread_fairness_audit.csv`: 43 rows, 0 failures.
- `objective_convention_audit.csv`: 43 rows, 0 failures.
- `no_instance_special_case_audit.txt`: passed.

Built-in tests run:

- `audit_bpc_certificate.py --self-test`
- `build\ExactEBRP.exe --method certificate-basis-test`
- `build\ExactEBRP.exe --method option-consistency-test`
