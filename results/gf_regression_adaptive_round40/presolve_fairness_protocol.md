# Round 40 presolve fairness protocol

The frozen comparison uses Gurobi 13.0.2, one thread, Seed 0, relative and
absolute MIP gaps 0, the same generated compact formulation, the repository's
process-wall timing convention, and the same machine. The predeclared witnesses
are one short Round-39 P-GRB regression and one C6-positive control.

The four paired arms per witness are P-GRB/C6 with Gurobi `Presolve=0` and
P-GRB/C6 with Gurobi `Presolve=-1` (Auto). `--global-gini-tree-presolve off`
is retained as a frozen legacy safety option but does not control the Gurobi
fixed-interval backend used by C6.

All 8 rows passed parameter readback, one-thread, seed-zero,
zero-gap, original-problem verification, finite-bound, and strict-certificate
gates. The uniform policy frozen for Parts 1--3 is **Gurobi Auto (-1)** for
plain Gurobi and every C6 Gurobi optimize phase. No instance dispatch is used.
