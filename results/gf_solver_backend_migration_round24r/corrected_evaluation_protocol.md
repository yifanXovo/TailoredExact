# Frozen Round 24R evaluation protocol

This protocol was frozen after implementation/mechanical qualification and before any official Stage 1 or Stage 2 performance run. Runs are serial, one thread, and process-wall limited. HGA, model generation, optimize calls, logging, and finalization count against the stated budget.

## Arms

- `P-CPX`: plain complete original compact MILP, CPLEX default/on presolve, no HGA/external UB.
- `P-GRB`: the same canonical complete original compact MILP, Gurobi Presolve `-1`, Seed `0`, exact-zero relative/absolute gaps, no HGA/external UB.
- `S0-SAFE`: corrected persistent CPLEX S0/F0 with presolve/Reduce/Linear off.
- `T-CPX-ST-PON-DIAG`: persistent CPLEX presolve-on research diagnostic; permanently non-certifying and its bounds are non-authoritative.
- `T-CPX-EXT-PON` and `T-CPX-EXT-POFF`: solver-neutral external tree using cached immutable static CPLEX leaves, respectively presolve on and off.
- `T-GRB-EXT-FRESH-COLD`: fresh Gurobi native model per attempt from the cached artifact, no explicit start.
- `T-GRB-EXT-COLD`: retained unchanged native model per leaf, no explicit cross-model start.
- `T-GRB-EXT-WARM`: the cold lifecycle plus complete independently verified same-run starts for compatible newly created models.

All tailored arms use the same same-run independently verified HGA incumbent, non-strict cutoff, Gini root range, initial intervals, split geometry/depth/width, interval row factory, F0 formulation, parent-bound inheritance, scheduler, and process deadline. The single-tree/external-tree comparison is an architecture comparison, not a pure restart-only ablation.

## Stages

- Stage 0: clean release builds with and without Gurobi; all C++ and Python tests; two independent process-local license checks; toy P-CPX/P-GRB exact comparison; toy and V12_M1 native import/domain audit; external-tree/cache/status tests; and static no-dispatch scan.
- Stage 1A: `moderate_seed4301`, six prescribed arms, 120 seconds each. It is a correctness sentinel and excluded from aggregate performance claims.
- Stage 1B: `V12_M2`, fresh-cold/retained-cold/retained-warm Gurobi, 120 seconds each.
- Stage 1C: `V12_M1` and `V12_M2`, S0-SAFE/T-CPX-EXT-POFF plus non-authoritative T-CPX-ST-PON-DIAG/T-CPX-EXT-PON, 180 seconds each.
- Stage 2: exactly four prescribed instances crossed with seven prescribed arms, 300 seconds each, only after relevant gates pass.

Correctness-valid comparisons prioritize strict original-problem certificate, certificate wall time, valid global LB, common-UB gap, common-UB bound-progress AUC, and gap-threshold time. Native objectives/bounds, verified UBs, and reporting-only common UBs remain separate. Invalid rows remain in evidence and are excluded by the frozen validity rules; no instance, arm, or budget may be replaced after observation.

Every Gurobi subprocess inherits `GRB_LICENSE_FILE=E:\gurobi\gurobi.lic` only in its process environment. Gurobi environments use silent pre-license startup; native logging starts after license acquisition so license identifiers are never serialized.
