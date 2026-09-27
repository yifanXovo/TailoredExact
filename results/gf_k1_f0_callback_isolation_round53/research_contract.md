# Round 53 frozen research contract

Round 53 is a preregistered, gated study on Round 52 head
`44ed4057cc4d2ce67b86d623b57500e95cad5058`. It asks whether the uniform
F0-CLEAN interval-MIP formulation should replace production v0, what proof
value the removed exhaustive subset-duration rows provided, which part of the
rejected Round 52 callback path caused regressions, and—only after fixed-MIP
qualification—whether unchanged K1-AM benefits on a new sealed V12 panel.

F0-CLEAN is frozen before results as
`interval-mip-core-no-exhaustive-subset-duration`: it removes only the
historical exhaustive subset-duration strengthening family, adds neither the
Round 52 static rank-2/rank-3 block nor a dynamic callback, leaves PreCrush at
its default, and preserves all other variables, rows, bounds, objectives,
interval/cutoff semantics, symmetry, branching, and solver settings. It is
uniform at every instance size. Historical v0 happens not to write the target
family for V>12, so equivalence there is a mathematical consequence, never a
dispatch rule.

The K1-AM outer controller is immutable: K0=1, one complete strict-improver
interval, midpoint refinement, adaptive-mass tau=0.08, and the Round 47 native
target, exact-parent closure, infeasible-child, coverage, bound, and strict
certificate lifecycle. All rescues, alternative points, symmetry/branching
research, M1, and additional cut families remain off.

Every official row uses the same executable and complete minimization
objective with Presolve=Auto, Seed=0, Threads=1, MIPGap=0, MIPGapAbs=0,
certificate tolerance 1e-7, verified incumbent/cutoff contract, honest
total-process accounting, and no known-optimum/archive-winner injection.
Ordinary caps are at most 3600 seconds. Only the four sealed tight-T instances
may trigger the frozen all-arm 7200-second extension.

Stages open only through their written gates. F0 itself may never be revised.
At most one uniform rescue, selected from R1/R2 using LP/callback diagnostics
rather than runtime wins, may open. No algorithm change is permitted after
fixed confirmation opens or after the sealed panel opens. Negative and mixed
conclusions are valid outcomes; witness-, size-, identity-, time-, Work-,
node-, memory-, or hardware-dependent actions are forbidden.
