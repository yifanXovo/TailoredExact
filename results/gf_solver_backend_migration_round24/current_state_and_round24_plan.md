# Round 24 current state and plan

Round 24 is a solver-backend feasibility and mechanism-isolation round. It cannot promote a new stable mainline. The corrected CPLEX S0/F0 configuration remains `S0-SAFE` throughout.

## Frozen starting state

- Authoritative checkout: `E:/codes/ExactEBRP`
- Starting branch: `codex/round23-moderate4301-correctness-unified-convergence`
- Round 24 branch: `codex/round24-gurobi-baseline-external-tree`
- Local branch base: `a977efe52a79877c057ce8e3421901979d16f1be`
- Observed remote main: `f115e9bb600f68e5368df78f06203331a800a33b`
- Merge base: `a977efe52a79877c057ce8e3421901979d16f1be`
- Git source tree for local base, merge base, and remote main: `625acf423cae776c31b40c5d283f47da0b6c9c7b`
- Relationship: remote main is two merge commits ahead, while all three source trees are byte-identical.
- Existing staged changes: none.
- Existing tracked content changes owned by the user: the two `exact_moderate_seed3301_1200s_static300` evidence files listed in `source_of_truth.md`.
- One additional status-only line-ending/stat observation exists for `handling_convention.json`; it has no content diff and is treated as user-owned.
- All pre-existing untracked files and directories are preserved.

## Pre-change gates

- Eight C++ test executables passed with zero failures: 111 groups/requirements.
- Six Python/regression suites passed with zero failures: 107 groups/checks including the isolated handling-convention check.
- CPLEX 22.1.1 is locally available.
- Gurobi 13.0.2 is installed at `D:/gurobi1302/win64`.
- The initial minimal Gurobi optimize call failed with error 10009 because no license was found.
- No `GUROBI_HOME` or `GRB_LICENSE_FILE` environment variable and no license file at the standard audited locations was found. No license file contents were read.

The missing-license result blocks official performance runs under the preregistered Stage 0 rule unless a license becomes available without installing or downloading another solver. Implementation, compilation, fail-closed tests, canonical-source audits, and non-Gurobi diagnostics continue; unavailable official rows will remain explicit rather than being synthesized.

## Work sequence

1. Add optional Gurobi build discovery without vendoring proprietary files.
2. Expose one canonical compact LP writer to both native backends.
3. Add the plain Gurobi backend, progress capture, and fail-closed engineering-exact status adapter.
4. Reuse `ControllingLeafScheduler` in a solver-neutral external Gini controller.
5. Add static CPLEX and Gurobi fixed-interval backends, retained-leaf lifecycle instrumentation, and verified cross-model starts.
6. Add the Round 24 safety override for the explicitly known-unsafe CPLEX presolve-on diagnostic while protecting S0-SAFE defaults.
7. Freeze and commit manifests before any eligible official performance result.
8. Run Stage 0 and only proceed through the official stages if every blocking gate passes.
9. Publish all required audits, comparisons, exclusions, and final decisions on the Round 24 branch using a normal push.
