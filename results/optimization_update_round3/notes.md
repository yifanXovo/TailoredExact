# Round-3 Notes

- Work started from local `main` after fast-forwarding to `7f2f86c`.
- No pre-existing uncommitted local changes were present before this pass.
- CMake was not available; fallback `g++` builds succeeded for `ExactEBRP.exe` and `ExactEBRPCompare.exe`.
- V4 smoke diagnostics completed. `gcap-frontier` on `gcap_smoke_V4_M1.txt` remains certified with `status=optimal`, `gap=0`, verifier passed, and original full improving Gini range coverage.
- Local runnable V8/V10 text instances were not present. Existing V8/V10 JSON files are historical artifacts, not runnable source inputs for this ablation.
- V12 M1 and V12 M2 short ablations remain noncertified. Improved full settings produce lower-bound progress only:
  - V12 M1 average: LB `0.253246606270`, UB `0.379830913219`, gap `0.333264888517`.
  - V12 M2 average: LB `0.473381644940`, UB `0.779342269192`, gap `0.392588258519`.
- The new Gini range fields report `frontier_range_certificate_scope=original_full_improving_range` for the V12 ablation runs, but they are still not certificates because intervals remain unresolved and the global gap is positive.
- Initial V12 M1 incumbent tests exposed an address fault (`-1073741819`). The fault was captured with gdb and fixed by rejecting malformed incumbent-pool columns whose operation vector was missing or too short.
- Post-fix `--bpc-incumbent pricing` and `--bpc-incumbent portfolio` repros exit with code 0 and write JSON.
- Imported incumbent audit on `results\closure7200_v12_m1_average_strong_bpcseed.json` did not verify against the local regenerated V12 M1 input, so it was not accepted as an incumbent.
- CPLEX was not used in this pass; these are BPC/frontier diagnostics and ablations only.

Summary files:

- `before_after_summary.csv`
- `ablation_summary.csv`
- `incumbent_audit_summary.csv`
- `interval_ledger_summary.csv`
- `notes_incumbent_failures.txt`
