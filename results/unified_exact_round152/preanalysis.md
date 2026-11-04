# Round152 preanalysis, before new solver results

The adopted task is goal.md (user supplied, 4 November 2026 Asia/Shanghai).
The verified starting head is c6e930ffcb84f0c3801c651f28b5f7e8e2062f33.
Remote main remains b2b940c1e517a72e226ec60fc49ff19651737632 and does not
contain that head. PR213 is open, Draft and unmerged. This branch therefore
uses R151 as its temporary PR base. No tracked changes existed in the active
tree; historical untracked evidence is retained. The original workspace is
protected. No solver, compiler or PDF process was active at intake; two
existing UI server processes are unrelated and will not be stopped.

All new work is under E:/codes/ExactEBRP-work. The initial study is offline:
no production changes, recompilation, default changes or complete arms are
authorized by the current evidence gate. The stable method remains R137.
New experiments are serial, Seed 0, Threads 1; a single outer process fee
includes construction, optimization and its necessary checking. Native
Runtime/Work are not charged again. The ceiling is 86400 seconds. Failed
attempts remain charged and preserved. Theory and authoring/public I/O are
separate. H seed 20260626 applies only if complete arms are later admitted.

## Domains and questions

1. N-B35-S: difficult resource-deficit domain, inherited pure B initial LP
   from R150. Its physical inventory budget is obtained from the input,
   not from an LP solution. Reuse baseline and add AP with every variable free.
2. K-35-U: historical surplus domain. Restore R135 AP evidence and its original
   full B domain. Compare objective, bounds, cutoff, row semantics and column
   names against the retained root; reuse only if these agree. Otherwise keep
   the historical domain explicitly distinct and pay for the needed reference.
3. N-C20-U: positive-target certificate role with no CPF root gain in R151;
   inherited pure B root and a new AP reference are required.

These choices precede new results. K20, RB35 or RX20 may be added only to
answer an identified structural uncertainty. No historical complete result
will be rerun. No saved incumbent or offline direction is a free online input.

## Method and attribution

First add the known AP aggregate. Then compare with the relevant GD,
shared-inventory and threshold-count information when a new direction is
promising. Keep this finite reference scope explicit; it is not the union
of all possible historical disjunctions or all route-hull cuts.

The necessary inventory oracle keeps actual integer supports, hard total
inventory, and physical G <= gamma_U. It prices max(gamma_L,G)+sum h-pi;
gamma_L is never a physical G lower bound. A zero inventory is handled
separately. Every positive denominator bin has a valid LB even when unsolved;
the global LB is the minimum across the entire cover and the zero state.
Feasible stocks give only pricing UBs after exact-objective reevaluation.
Restricted dual masters propose potentials; their intercept is never used
without global pricing qualification. Negative potentials/intercepts remain.

The first oracle uses denominator-bin MILPs. Bounds on S come from safe
inventory boxes and the hard resource; no LCM grid is used. A unary integer
resource DP supplies conservative fallback bounds and a projection control.
Bounded dual constraint generation may discover nonzero potentials.
Stopping uses separation/nonseparation certificates, uncertainty and a
declared iteration cap. Offline wall caps do not become online dispatch rules.

A meaningful deepening will address the observed bottleneck (pricing gap,
denominator error, projection compatibility, or weak directions). A small
root increment alone neither admits nor rejects production. Production
requires nonduplicate information and plausible cost, followed by independent
admission and new same-PE, own-H complete comparisons.

## Qualification and delivery

Small exact domains check resource versus average resource, feasible joint
marginals versus objective gaps, nonminimal completions, signed potentials,
zero states, bins and scope transport. R133 is only a known control. Strict
claims against a strong reference require the complete reference extension
or exact finite-domain optimization.

The independent reviewer is not the main implementer. The requested first
review covers formulas and this design before expensive experiments; later
reviews cover actual implementation and final data/claims. Native floating
qualifications follow R134; exact small proofs are reported separately.
Delivery includes source identities, expenses, all failures/undecided oracles,
paper text, a bounded new-evidence carrier and one public restore, RESUME,
English Draft PR, and bounded cleanup (zero deletion is acceptable).
