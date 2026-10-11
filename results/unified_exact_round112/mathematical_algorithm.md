# P-S correctness and exact-backend scope

Each vehicle departs empty. Each station receives at most one vehicle's single
nonzero-direction integer pickup p or delivery d. Prefix and return loads lie
in[0,Q_k], loaded return is allowed, and depot unloading is paid. Q bounds
instantaneous load, not cumulative pickup. Inventory satisfies
Y_i=b_i+sum_k(d_ki-p_ki),0<=Y_i<=C_i, and r_i=Y_i/D_i. There is no min_ratio
inventory floor. Travel is the original metric distance/1.5; complete route
duration is travel+(t_p+t_d)sum_i p_ki, including loaded return unloading.

F=sum_(i<j)|r_i-r_j|/(n sum_i r_i)+lambda sum_i omega_i|r_i-1|.
The original evaluator sets the G term to zero at zero denominator and retains
the penalty. Formal roles keep lambda=.15, pickup/drop60/60 and their original
max-normalized weights and raw input bytes. With positive lambda and weights,
nonnegativity and a zero penalty give F=0 iff Y=D. Numerical zero closure keeps
the inherited1e-7 policy; exact integer Y=D and the actual floating F are
reported separately. G50-C1 has a historical zero witness and exact L0; raising
that floor cannot repair lost primal completion. G100-R2's zero optimum is
unproved. The positive5/24 micro has zero handling and positive objective.

P-S invokes the original runPaperPrimalHeuristic via the existing standalone
diagnostic wrapper, configured with the exact R83 ENS preset: original24+1
construction, decoded descent, quantity/R76 physical closure and R83 exchange.
Its H options are distinct from the original cold compact options; the process
start time, absolute deadline, input, physical/numerical parameters stay common.
All work and mandatory output/verification are paid within the arm.

The original solveGurobiBaseline writes the actual strengthened=false cold
canonical spec, preserving numeric rows, columns, types, bounds, objective,
exhaustive-block strategy and native defaults. No state/F0/A/B/true-G/cutoff
strengthening, LP probe, hints, priorities, bound target, Cutoff/BestObjStop/
BestBdStop/StartNodeLimit, or repeated Optimize is introduced. Fresh reference
LP equality and full pre/post native arrays independently check this claim.

Equal-Q vehicle normalization is the inherited stable operation-count order
within genuine capacity classes. No unequal-Q relabeling occurs. Empty vehicles
keep original IDs and all their zero native columns. The existing mapper fills
every actual original column, including unvisited quantities, x/z/mode,
load/order, Y/r/e/h, bit/prod/zprod and present original auxiliary columns.
Unknown columns reject. Finite values, original bounds/types, every actual row
and original objective are checked before one complete GRB Start submission;
all columns are read back. Full native numeric matrices and name metadata must
remain identical. No solver repair substitutes for this external validation.

Any legal complete H fleet is own primal U from its verified availability;
native failure to produce a new incumbent does not erase it. The best own legal
fleet is retained and every native witness is independently physically replayed.
API/mapping/evidence failures reject P-S rather than falling back to cold. If
H satisfies original zero closure, own witness plus F>=0 ends with startup_zero
and no exposed native backend. Otherwise precisely one original compact MIP is
allowed if the unchanged work window remains. No duration resets at handoff.

Warm Start is primal information and leaves the same original integer problem
and exact backend. Its solver-induced presolve/search effects are measured.
Global L comes from qualified full-original native evidence or independent0;
local status/rc alone is no certificate. Proven numerical contradiction rejects
all native lower claims of the damaged call and dependent conclusions, retaining
independent floors. Signed U-L is never clamped. Complete certificate closure
uses inherited1e-7; it is numerical native certification, not rational proof.

ENS/M-B retain original true-G scopes, cutoff epochs, full improving-domain
cover, AM=.08 and integer-type restoration. M-B's continuous-declared p/d remain
integer at a complete solution because integer b/Y, unique binary assignment
and nonzero direction force quantity|b-Y|. Its original A/B rows are valid
strengthening but are not required for that implication. This proof does not
extend to fractional inventories or split/simultaneous service. Their scoped
LP/MIP claims remain independent and full cover must discharge every obligation.
