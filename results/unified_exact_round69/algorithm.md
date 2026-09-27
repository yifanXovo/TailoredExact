# Round69 frozen algorithm

No solver implementation or parameter change is introduced in this validation.
VD-S uses the unchanged `research-round68-vdp-start`: canonical paid HGA and AM, Round67
VD-P one-hot inventory-state products, and one current complete verified Start
before every required native MIP. VD-P disables only this new Start path.
K1-R uses `research-round65-k1-h` with the same reliability fixes and no resource
policies. Original P-GRB remains the primary reference with native defaults.

1. Start the whole-run clock, parse original inputs and check the inherited
   metric travel and nonnegative-penalty applicability requirements.
2. Run full HGA with seed20260626, population24, decoder10, stagnation2000.
   Verify and retain physical routes/operations. Verified F=0 may close against
   the universal zero lower bound. All startup and validation costs are paid.
3. Build the complete Gini cover with K0=1. Keep AM's midpoint rule, normalized
   closure threshold0.08, depth cap8, width floor1e-4 and mathematical targets.
   Logical limits send unresolved obligations to complete MIP, never discard them.
4. Use the exact VD-P model with node prefix loads and all inherited valid F0
   blocks. LP calls retain the original type restoration and coverage rules.
5. Before each needed MIP, including a retained LP model, clear explicit Starts.
   Normalize only interchangeable equal-Q vehicles in the current paid witness,
   reverify physical semantics, and map every actual model column. If its Gini
   interval/cutoff is incompatible, skip the witness while keeping the obligation.
   Otherwise check all bounds/types/rows and objective, submit one complete Start,
   and read every value back. Unexpected integration failures fail qualification.
6. Refresh only the remaining whole-run deadline. Gurobi performs full MIP
   search; read-only telemetry distinguishes submission, native log acceptance
   and MIPSOL vector observation. Mathematically qualified target stops are
   allowed. Global LB comes from the complete frontier; UB needs physical routes.
7. Certify under the existing numerical standard when all obligations close.
   At the single experiment deadline end the whole algorithm with valid bounds.

The added path has no learned instance gate, search-policy tuning, construction,
local time/Work cap or restart. NumStart/StartNumber select the one vector, not
a new search policy. Clearing explicit Starts does not erase Gurobi's separate
previous-solution reuse. No ARC, LOG, PREFIX, extra resource cuts or budget
features are inherited. Model mapping cost and evidence writes consume the run.

All arms: Gurobi13.0.2, Threads1, Seed0, PresolveAuto, requested gaps0 and the
original numerical tolerances. Algebraic correctness and finite numerical
checks do not imply a rational certificate, novelty or a runtime improvement.
