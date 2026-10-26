# DS-X: finite decoded descent with inter-route tail relocation

Formal candidate: research-round71-vds-interroute-descent. It is isolated and
default-off, with source/binary identities in build_v1.json. DS is the fresh
intra-route ablation research-round70-vds-descent. Both share the same seed,
decoder, proof model and controller; DS-X uniformly adds the existing finite
cross-route tail neighborhood. No instance-specific switch is used.

1. Generate24 random station permutations and vehicle separators at seed20260626,
   and fully decode all initial chromosomes with the existing deterministic
   greedy operation decoder. The24 seeds define the sampling algorithm.
2. For each seed, construct the existing guided intra-route candidates and the
   eligible cross-route tail relocations described below. Order by the existing
   proxy, fully decode each inspected candidate and accept the first fitness
   improvement greater than1e-12. Restart that seed's neighborhood after a move;
   otherwise exhaust all generated candidates and finish the seed. The proxy
   never rejects candidates or certifies feasibility.
3. Publish each global improvement through the independent physical verifier.
   Retain only a verified original route/operation witness. Stop startup after
   all24 finite descents, a whole-run deadline, or a verified numerical zero.
   An interrupted descent is explicitly incomplete, never local exhaustion.
4. Feed the retained verified UB to the inherited VD-S one-hot Gini-product
   formulation and AM proof controller. Before each compatible actual MIP,
   map the witness to a complete Start, verify rows/types/objective and API
   readback. Gurobi remains the complete MIP engine. Starts supply primal
   points and do not establish lower bounds.
5. Preserve full original-domain interval coverage and every proof obligation.
   Report the physical UB and legal full-frontier LB. A pre-proof whole-run
   deadline can retain analytical LB0 only when all original nonnegativity
   premises hold. Original numerical certification is not a rational certificate.

The neighborhood uses the longest travel-plus-return prefix fitting the
input's mathematical T. Decoded drop/pickup service anchors and the existing
supply/demand role classification guide insertion. Full decoding, including
handling and prefix loads, determines actual feasibility and fitness. DS-X
additionally relocates the first eligible unused-tail supply or demand node
between vehicle sequences to an eligible service anchor. It preserves unique
station assignment. It is a limited neighborhood: it does not enumerate every
served-node relocation, exchange, or operation quantity. Duplicate candidates
can remain; cache hits still count as inspected full-decoded candidates.

The result and descent CSV separately record generated cross-route candidates,
decoded cross-route checks and accepted cross-route moves. This qualifies the
actual mechanism beyond an enabled flag. A terminal pass checks all its
generated candidates; an improving pass may stop on its first strict gain.
Cache and fresh decoding must agree. Finite strict descent gives termination
for the fixed decode map, not global optimality of the heuristic neighborhood.

The unchanged first-class AM rules use one initial interval, midpoint splits,
normalized balanced child-bound closure threshold0.08, depth limit8 and minimum
width1e-4. Parent/child LP bounds define normalized gain scores; the threshold
admits a complete child partition. Small strict gain can set a mathematical
native-bound target; no strict gain retains full parent closure. Decision-score
clipping never clips a reported legal bound. The old round47tau0.07915 field is
inactive compatibility metadata. No runtime, Work, credit or hardware rate
controls these mathematical choices.

Every construction, proxy, full/cache decode, verification, build, LP/MIP,
mapping and exit cost is included in process wall. There is no evolutionary
startup, restart, local time slice, larger population or historical selection.
The legacy hga-full container label is compatibility metadata; actual stop mode
is decoded-descent-interroute, with zero HGA generations. The backend admits
this exact mode/preset/seed24-start contract while preserving old variants.

P-GRB is original compact/native defaults, without HGA, explicit external
Start, new cuts or imported bounds. K1-R is research-round65-k1-h with the
existing reliability repairs. Shared measurement settings are Gurobi13.0.2,
Threads1, Seed0, PresolveAuto, requested gaps0 and original numerical tolerances.
All fresh arms use logical processor2/mask4; this is a measurement condition.

Correctness derives from admitted physical witnesses and the unchanged full
proof. Cross-vehicle allocation is a BRP design hypothesis. Complete paid
outcomes must establish its efficiency. Relocation, greedy decoding, multi-start,
one-hot encoding and native Starts are not claimed as new theoretical techniques.
