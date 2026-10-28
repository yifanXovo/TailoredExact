# Independent pre-run implementation review

Reviewer: `/root/independent_review`; review date 2026-10-29 (Asia/Shanghai).
This is a static source review. It starts no executable, compiler, Optimize or
native library. Actual matrix qualification and per-run parameter receipts
remain separate requirements.

## Reviewed version

| File | SHA256 |
|---|---|
| `include/Round138Research.hpp` | `6e322856d47d807f16f8d8f86bf6b739df3f576fb0d0a0b5aa75ae7be4c77046` |
| `src/CplexBaseline.cpp` | `6a598b199b70cec303bc4a1e83bbc7397895381a7be9f8b9e9eb3f75ab9b8695` |
| `src/main.cpp` | `13f86cf3969a112f4d9b007756d183270021074af99f696d7d618d270718c269` |
| `scripts/round138_build.py` | `8b599cb4f2dd3ba1efa79e673a8ef3cbfdd26ae64b0a507f9db975faa8fbdf24` |

The generated `scripts/round138_export.cpp`, inherited
`scripts/round122_prepare.py`, `scripts/round137_campaign.py`,
`src/PaperK1AmSf.cpp`, `include/Round127Research.hpp`,
`include/Round137Research.hpp`, `src/PaperExternalGiniTree.cpp`,
`src/GurobiBaseline.cpp`, `src/Round50IntervalMip.cpp`, and relevant parser
types were also read to trace actual calls rather than relying on comments.

## Decision

**ACCEPT for targeted matrix/parameter qualification.** No source-level
mathematical or execution-path blocker was found. This is not an unconditional
admission of an as-yet uninspected formal experiment matrix.

1. The new process-local switch defaults to false and does not change
   `SolveOptions` layout. Production CLI selection requires explicit `ms2`.
   The writer further requires strengthened shared M-B/VD-P states. Its disabled
   branch inserts no variables, rows, statistics or readback files.

2. `writeCompactLp` computes stock from indices `1..V`, excluding depot 0.
   `Instance::Q` has exactly M vehicle entries. `Bminus=max(0,B-sum Q)` correctly
   permits loaded return; cumulative pickup does not appear. The four calls
   emit, in order:

   - `J-alpha*tau-Bminus*G >= -alpha*Bminus`;
   - `J-beta*tau-B*G >= -beta*B`;
   - `J-beta*tau-Bminus*G <= -beta*Bminus`;
   - `J-alpha*tau-B*G <= -alpha*B`.

   `zprodName(i)` is the unscaled inventory product. No target or weight
   coefficients enter these rows. `g_lb` and `g_ub` are the same actual bounds
   used to declare model variable G.

3. All new variable coefficients are assigned directly to the expression map
   and emitted through the existing `num`, which uses binary64 `max_digits10`.
   The emission deliberately avoids `addTerm`'s small-coefficient filter.
   Exact integer stock is checked against 2^53. Only the computed RHS product
   moves one representable value outward: upward for upper rows and downward
   for lower rows. This encloses the exact product of the stored binary64
   factors. Coefficients are not rounded or changed by that adjustment.
   Zero products are exactly represented and need no shift.

4. Root and child canonical models share the same writer. In
   `PaperExternalGiniTree::ensureArtifact`, each new spec receives the actual
   leaf interval and verified cutoff. A cutoff-epoch change checks the old
   immutable file, discards the backend leaf and all LP/child state, and invokes
   canonical construction again. The generated canonical SHA and row signature
   cover the whole ordered file after emission, so both the switch and interval
   coefficients enter model identity without a separate Boolean cache key.
   The switch does not change within a formal process.

5. The retained Gurobi leaf rejects a changed canonical SHA. The LP path
   captures original VTypes, changes them to continuous and restores them before
   retaining the object. It does not remove the four stock rows. Terminal and
   partial-target MIP requests reference the same artifact/SHA. Actual exports
   and native type/readback receipts should still verify this on representative
   root/child/refresh models; static reachability alone is not runtime evidence.

6. The inherited launch builder replaces the single `--gurobi-seed` argument
   with the panel's explicit Seed. Main parses it before presets. Inspection
   of the actual research-round83 -> paper-K1 preset chain found no assignment
   overwriting `gurobi_seed`; the post-preset R138 readback reads the resulting
   option. H separately receives the established `20260626` seed.
   `configureRound50IntervalMipV0` contains an unrelated hard-coded Seed0,
   but that function is not called by the inspected formal paper preset path.

7. The formal tree passes the complete `options` object into
   `makeGurobiFixedIntervalBackend`; its constructor copies it, sets Seed on the
   native environment and reads it back, failing the configuration gate on any
   mismatch. Child model environments inherit that configured environment.
   Before native evidence is admitted, `evidenceParameterReadback` reads the
   actual model environment's Seed and compares it with `options_.gurobi_seed`.
   Thus Seed1 is not merely a filename or manifest label. Per-run native
   receipts must demonstrate the actual effective value.

8. The build verifies inherited object/archive/compiler/DLL hashes, replaces
   only `CplexBaseline.o` and production `main.o`, and links into the distinct
   Round138 cache. Frozen R137 executable/object paths are read and retained.
   The generated exporter uses the same new writer and has no Optimize call.
   Its native metadata inspection does load the installed DLL; this is distinct
   from this review, which loaded no vendor code. Each exporter invocation is
   a fresh process, so the process-local Boolean cannot leak between variants.

## Follow-up evidence required before long runs

- Actual disabled-build comparisons against frozen R137 on representative
  root, child and cutoff-refresh domains; candidate-on differences must be
  exactly the declared four rows and unchanged variable types/objective/bounds.
- Validity checks on loaded-return/depot/zero/degenerate/heterogeneous cases,
  including actual RHS/coefficients rather than only displayed formulas.
- Frozen full-position commands must preserve rho=1 resource objectives and
  explicit Seed0/limited Seed1, AP off and all other GI-TBC settings. The CLI
  can technically combine research flags, so the plan must demonstrate that
  the main comparison changes only stock RLT.
- Actual native model-environment parameter/readback evidence and model
  identities from any entered LP/full runs.

## Readable historical carriers

The current paper sparse checkout need not contain the archives. The following
local files were checked to exist without restoring or rewriting anything:

- `E:/codes/ExactEBRP-work/worktrees/round132/results/unified_exact_round132/artifacts/complete_tiny_joint_study.zip`.
- `E:/codes/ExactEBRP-work/worktrees/round134/results/unified_exact_round134/artifacts/math_failures_and_costs.zip`.

For the earlier exact review I used `git show` directly into Python memory:
the tiny carrier at fixed pin `52b02252ba47e8228b73e071d6ed692385a4f816`,
and the R134 math carrier at the R138 starting HEAD. The necessary math member
is `results/unified_exact_round134/math/tiny_exact.json`. The SHA256 values
are recorded in `pre_math.md`; verify those before reusing either local path.
