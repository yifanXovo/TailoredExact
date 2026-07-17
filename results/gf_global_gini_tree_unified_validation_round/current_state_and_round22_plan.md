# Current state and Round 22 execution plan

Round 22 starts from live GitHub `main` commit `f123418f9ae50c7bd5d09616757cd56d18cb3906`, whose tree contains merged Round 21. The work branch is `codex/round22-engineering-certificate-dense-trajectories`. Pre-existing modified and untracked files are excluded from Round 22 staging and remain untouched.

Implemented mechanical changes are the engineering-exact certificate classifier, a versioned complete-model correctness gate, clarified independent verifier fields, full residual diagnostics, shared buffered dense CPLEX progress capture, canonical checkpoint primitives, and deterministic unit tests. The held-out suite, arm manifests, protocol, and instance hashes are frozen before production.

Execution is serial: clean release build and all mechanical audits; live callback and matched overhead gates; 24 existing-suite rows at 900 seconds; 24 existing-suite rows at 1,800 seconds; 18 held-out rows at 900 seconds; then only preregistered conditional 3,600-second comparisons. Every official row uses one frozen executable, exact-zero relative/absolute gaps, one thread, one fixed manifest, and dense progress. Excluded/interrupted/pre-freeze attempts remain outside official summaries.
