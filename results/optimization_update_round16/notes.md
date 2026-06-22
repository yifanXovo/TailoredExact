# Round 16 Notes

This pass consolidated configuration and reporting rather than adding a new pricing engine.

Implemented:
- Added `RunConfigSnapshot` as the single resolved configuration source for JSON, notes, and progress logs.
- Added `--algorithm-preset` / `--production-preset` with `paper-bpc-core`, `paper-exact-portfolio`, `paper-bpc-experimental`, and `diagnostic-large`.
- Added option audit fields and `option-consistency-test`.
- Added instance scope/hash/source fields.
- Added conservative incumbent archive scanning. Only reconstructable route plans that pass the independent verifier can be selected; objective-only rows are ignored.
- Added result module fields for BPC, compact, and portfolio certificate summaries.

Safety findings:
- A default scan over the entire `results` tree initially exposed a Windows heap-corruption exit (`-1073740940`) through old heterogeneous artifacts. The scanner was hardened to skip large files, JSON without routes, and JSON for a different instance before route parsing. Post-fix default and explicit archive scans exit cleanly.
- No address/memory error signatures were found in the final Round 16 raw JSON/progress/log files.
- V4 `gcap-frontier` remains certified with objective `0` under core, exact-portfolio, and experimental presets.

Ablation scope:
- Full 300s rows were run for V12 M1/M2 core, experimental, and exact-portfolio BPC entries, plus compact companion rows for V12 M1/M2.
- The eight-variant component ablation was run on V12 M2 at 60s as a controlled companion matrix. Running the full eight-variant 300s matrix across V4/V8/V10/V12/V20 was not affordable in this pass; this limitation is explicit in the paper report and attempt log.

Decision:
- Two-track relaxed-RMP remains appendix/experimental and disabled in `paper-bpc-core`, because it did not produce a certificate-valid lower-bound improvement or relaxed-pricing closure on the nontrivial rows in Round 14/15/16.

CPLEX/compact:
- CPLEX plain benchmark was skipped. Compact/tailored companion rows were run for V12 M1/M2 under the exact-portfolio preset, but they did not certify within 300s on the regenerated instances.

Documentation:
- Added `docs/paper_algorithm_chapter.md` and copied it into this result directory.
- Added `docs/experimental_two_track_assessment.md`.
- Updated the proof, certification protocol, paper report, attempt log, and README with Round 16 preset and certificate-scope rules.

Audit:
- `result_integrity_audit.csv` reports zero failed rows.
- `option_consistency_summary.csv` includes V4 and V12 two-track checks. JSON, notes, and progress-facing fields all use the resolved `RunConfigSnapshot`.
