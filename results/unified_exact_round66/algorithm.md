# Formal candidate and controls

ARC = paid K1-R controller with the arc-load replacement formulation.
K1-R = the canonical full-HGA K1-AM configuration plus verified event retention
and immediate termination when an original-route witness has objective zero.
No preset defaults are changed. The experimental CLI explicitly enables ARC.

1. Parse the original instance and start the common whole-run clock.
2. Run the canonical HGA with its fixed logical stagnation/population rules.
   Verify and retain original route/operation witnesses. If a verified witness
   attains the universal lower bound zero, certify and finish.
3. Build the initial complete Gini interval cover (K0=1). For each required
   interval, use the canonical K1 bound contraction and midpoint AM rule,
   including its balanced normalized closure threshold 0.08, depth cap 8,
   and width floor 1e-4. These have the inherited mathematical/empirical
   meanings; the depth and width caps send unresolved domains to full MIP.
4. In every interval LP/MIP, retain the F0 objective/cutoff/route/order/duration
   blocks, replace node-load recurrences with station-origin arc loads, and
   treat node load as a derived continuous variable. Use complete Gurobi MIP
   searches as required by the controller. Native mathematical bound targets
   may terminate a solved proof obligation; preserve all remaining coverage.
5. Publish only independently admissible original-route UB and a bound backed
   by complete frontier coverage. Finish with the existing numerical
   certificate when all necessary obligations close.
6. At the single global experimental deadline, end the entire run and save
   the legal partial state. No component receives a separate resource share
   followed by resumption, fallback, or model selection.

All Round65 credit, optional proof budget and projection controls are off.
All Round62/63/64 resource formulations are off except that ARC reuses the
Round64 q-row writer to implement its mathematical replacement. This reuse
does not enable any old budget/controller behavior.

P-GRB is the original compact model with native default heuristics and no
algorithmic starts or cuts. K1-R isolates the formulation change. Q-PLUS, if
measured, retains the old node-load recurrences and integrality while appending
the identical q block; this is an ablation, not another selectable final mode.
Literal K1-AM remains available. Current runs have fixed solver seed zero,
one thread, automatic presolve, zero requested gaps and unchanged numerical
standards. Fixed logical HGA seed is 20260626.

Mathematical equivalence and scope are in mathematics.md. Standard commodity
flow is not claimed as novel; full-run performance is an empirical question.
