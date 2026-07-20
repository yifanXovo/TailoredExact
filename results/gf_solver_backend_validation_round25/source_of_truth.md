# Round 25 source of truth

Round 25 starts from local commit
`d52e340ef62be2bc2f248a1c5ad93cbbb75c6920` on
`codex/round24r-licensed-gurobi-qualification`.  The dedicated working branch is
`codex/round25-longer-multiinstance-backend-validation`.

The inspection-only fetch observed `origin/main` at
`639c3772687d4a22e6b2cf3daa4d16c03d015ecd`, exactly the expected merged Round
24R commit.  Its merge base with the local starting commit is the local starting
commit.  The two commits have identical Git tree
`fda2e7ce60ae1e5ea89b2c9237b379e320e2a261`; no pull, merge, rebase, or source
replacement was performed.

The authoritative inputs are the existing local checkout, the committed Round
25 protocol and manifests in this directory, and the two isolated release
executables recorded in `round25_build_manifest.json`.  The Gurobi-enabled
executable is frozen for every official and diagnostic row.  The CPLEX-only
executable is a qualification control.

The frozen solver executable was built from implementation commit
`2017358042c48c44c4386256a904bba0f3bcbf85`; the protocol/manifests were frozen
in `9268330c883a58d6674caebad04c19751417a947`.  The later sanitized-license
harness correction (`b6b8a584`) occurred before any official row and changed
only qualification classification.  The later metric-extraction correction
(`1f481b4b`) and final analysis/package work change reporting only: they do not
alter the frozen executable, mathematical options, row order, trigger inputs,
or any retained solver result.  The final package audit independently restores
and hash-verifies every compressed artifact.

Pre-existing tracked modifications and untracked paths were present before
Round 25.  They remain user-owned and are excluded from all Round 25 commits.
The provenance snapshots in this package document them without modifying their
contents.

The authorized Gurobi license is exposed only as `GRB_LICENSE_FILE` in child
process environments.  Its file is never opened, copied, hashed, printed, or
serialized.  Audit output records only nonsensitive booleans and return codes.
