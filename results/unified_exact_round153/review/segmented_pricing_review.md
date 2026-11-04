# Independent design review of denominator-segmented pricing

Reviewer: `/root/independent_review`, 2026-11-04 (Asia/Shanghai).

Latest gate: **ACCEPT_FOR_K35_SEGMENTED_RESEARCH**, after the concrete source
and `segmented_v1` qualification review recorded in the final addendum below.
The earlier design-stage pending decisions are retained as review history.

Verdict: **ACCEPT_DESIGN_FOR_TARGETED_QUALIFICATION; RESEARCH_INTERFACE_GATE_PENDING**.
The proposed four-segment positive-denominator cover is a valid decomposition
of the full price bound when implemented as below. It is a research-only
alternative to the current complete price, not a change to Q, the RMP
certificate or the frozen production helper. At this review no new segment
implementation or executed qualification result was available. The reviewer
read the existing `s_bounds` and frozen Oracle code; no Native call or
computation was run.

## Coverage and true integer embedding

Use `s_bounds.lower_exact` and `upper_exact`, interpreted as Fractions of the
actual binary64 ratio coefficients. The lower bound is at least both the
hard-resource denominator lower and the smallest positive supported ratio
contribution; it therefore covers every positive S. Zero is separate.

Partition this exact positive range into four rational closed intervals
`[S_j^lo,S_j^hi]`, with no gaps and shared endpoints. For a singleton range,
one nonempty closed interval suffices. Do not introduce a segment with a
zero lower endpoint and then divide by it. Save the exact endpoints and
check the coverage combinatorially, not with a floating tolerance.

For a true legal inventory with S in a declared segment, the normalized
embedding is

`t=1/S`, `x_iy=1[Y_i=y]`, `w_iy=t*x_iy`, `z_i=t*Y_i`, `r_i=c_i*z_i`.

The outward bounds

`t_low=down(1/S_j^hi)`, `t_high=up(1/S_j^lo)`

contain this embedding. Changing t's explicit bounds, every w upper bound,
and the x coefficients in all `w_lb`/`w_ub` rows consistently therefore
preserves every true point in that segment. At integral x, one-hot and
`sum_y w_iy=t` still force the same product; normalization forces `t*S=1`.
The resulting numerical segment may include a small enlargement outside
the exact S interval, which is conservative for its lower bound.

The original full-state, hard-total, Gupper, count and global TS rows remain
valid in a segment. The additional four TS rows use the local outward t
bounds and unchanged hard-total endpoints. Their selector coefficients must
use the already reviewed per-station one-hot error transport: the sum of
stationwise minimum coefficient errors for a `>=` row, or maxima for a `<=`
row, with RHS rounded outward in the same direction. A smaller denominator
interval does not excuse this coefficient transport.

For a full-row integer control, set q to true f and pairwise absolute values
to their true normalized differences. Checking the actual saved binary64
matrix on all enumerated segment members then tests the new bounds, changed
product coefficients and segment TS rows together. Endpoint membership must
use exact S, including both adjacent segments when equality holds.

## Global lower and candidate upper identities

Let `D` be the same valid whole-domain hard-total DP lower. Each planned
positive segment must have a recorded lower `L_j`, from its qualified actual
segment model or from D. Unvisited, interrupted, unqualified or Native
INFEASIBLE segments retain D; none may disappear from the cover solely from
an unqualified solver status. True empty-segment proofs are unnecessary.

If zero is legal, let `Z` be its exactly evaluated price; otherwise omit Z.
The complete bound is

`L = max(D, min(L_1,...,L_k,Z if legal))`.

This is a full-domain lower because every positive legal inventory belongs
to at least one segment and every segment lower bounds all its true members.
Overlap is harmless. Filling a missing segment with D can make the aggregate
weak, but cannot make it invalid. If there is no positive range, handle only
the independently verified zero case; do not manufacture an empty min.

All returned stock candidates must be re-evaluated on the original complete
R and actual beta/d. Their minimum true price gives a **global** inventory
upper. A DP/warm candidate may lie outside the segment that returned it, so
it is not necessarily an upper on that segment's minimum. A child lower
larger than its attached global candidate upper is not a contradiction.

Only the aggregate parent may declare `complete_domain=true`. Child records
must declare their exact S interval, actual t bounds, `complete_domain=false`
and the global-only identity of any candidate upper. The RMP receives only
the aggregated complete lower and globally legal stocks. A single child
lower is never a substitute for a full-domain price in `C_Q+min(a_K,L_m)`.

## Required wrapper corrections to inherited Oracle semantics

Two existing Oracle conveniences need explicit adaptation:

1. It labels a result RESOLVED when its stored upper minus lower is small.
   With a segment lower and a potentially outside-segment global upper,
   that predicate has no segment-gap meaning and can even be negative.
   Replace the child decision/labels; never propagate this as segment or
   global closure. Only the parent compares its complete lower with the
   true global upper.
2. The original `zero_possible` handling automatically takes the minimum
   with zero in each positive model's result. To obtain genuinely positive-
   segment lowers, disable this only in each child's own bounds dictionary
   and combine the legal zero price at the parent. Leaving the zero term in
   each child would still be conservative, but would be a weaker bound on
   the segment and must not be misdescribed as a pure positive-segment price.

The global DP early-attainment shortcut may return a whole-domain lower
without a Native segment call. That lower remains safe for the segment even
if its attaining stock is outside it; record the shortcut and global upper
identity rather than implying a segment optimizer was found.

Update `self.t_bounds`, row-transport evidence and actual model identity after
the subclass changes its matrix. The saved MPS, call, return and coefficient
records must describe the modified model. Preserve all original records;
do not leave a child saved result claiming complete-domain price solely
because the inherited method normally writes that flag.

## Targeted control and next research decision

The proposed small full-enumeration control is sufficient in scope: check
exact range coverage and actual rows on every true integer member of each
segment, then verify the aggregated lower/true-global-min/global-upper
bracket. Include the zero branch when legal and a deliberately unavailable
segment represented by D so omission cannot silently strengthen the bound.
Previously qualified signed objectives, beta=0 and global numerical transport
need not be broadly rerun; focus any added objective case on this new segment
aggregation and candidate-upper identity.

For a useful K35 comparison, reuse a saved potential/beta and its existing
300-second unsplit price as the reference where practical. Record the warm
stock source, segment cover, individual bounds and aggregate improvement.
The split is not guaranteed to help: four weaker or unresolved pieces can
leave the global minimum limited by the weakest piece. That is an observed
pricing outcome, not a negative theorem about the hull.

Four 75-second Native caps sum to 300 seconds of requested solve time.
Construction, repeated DP, model readback, serialization and disposal still
belong to the actual outer charge and can make wall time larger. Execute
segments serially, close the current K35 run normally before the experiment,
and keep its columns, interval and completed costs. Do not overlap Native
work or change the frozen `round153_pricing.py`/common/helper identities.

After the new subclass/wrapper code and the primary agent's serially metered
small result are available, review those concrete interfaces before admitting
the K35 segmented research run. This design review does not itself admit an
unseen implementation or add an experiment to the frozen complete panel.

## Concrete SliceOracle/PartitionedOracle source review

The subsequently supplied `scripts/round153_partitioned.py`, SHA256
`3510cb9d08aaf9f835b07e0772803e15cdcfa6dd1308946d1744cd0a5983f3e8`,
was statically read in full. **ACCEPT_IMPLEMENTATION_FOR_TARGETED_QUALIFICATION**.
The K35 segmented research gate remains pending the primary agent's serially
metered small control. The reviewer did not execute that control.

The implementation improves on the initial global-only child-upper plan:
`SliceOracle._conditional_stock` first performs the original exact stock
check, then requires exact `lo <= S <= hi`. A fresh `FunctionType` for the
frozen `Oracle.price` code binds that filter and a metadata writer in its
own globals dictionary, with the original argument defaults. The original
module and its global functions are unchanged. The same filter applies to
DP, warm and Native pool candidates. Thus every accepted child stock is a
true member of the declared segment, and its outward-rounded upper is a
valid segment upper. `CONDITIONAL_RESOLVED` now has the correct interval
meaning; the original objection to a possibly outside-segment upper no
longer applies to this implementation.

The parent separately checks whole-R DP/warm candidates, combines all true
returned stocks, and handles a legal zero independently. Every child's own
`zero_possible` is false. The normalized t bounds, all w UBs and both
product-row x coefficients are changed together, local TS rows are added
with the same exact coefficient-error formula, and `t_bounds`/matrix
semantics are updated after the change. Global necessary rows are retained.

The metadata adapter transforms each record before it is first written. It
adds exact S limits, actual t bounds, local transport and frozen-core SHA;
Native calls are labeled positive-S slices and child result records have
`complete_domain=false`. The wrapper writes a restriction declaration
before the inherited core call. This is not a post-closeout rewrite of
already sealed evidence. The core source still hashes to
`8ed325356a9171a3e1aaafbc4a5c0526a764f0c35148dd6de2ea15d0d925e558`,
and the admitted production matrix is unchanged.

The parent initializes one lower per planned segment to exact whole-domain
DP before any solve. A whole-domain DP-attaining stock can stop the loop,
leaving all unvisited pieces at that valid fallback. It then takes the
minimum of all pieces and legal zero, maximum with D, and one outward lower
rounding. The reported whole-R upper uses true values and outward rounding.
Only this parent result is complete-domain. An exception produces no new
complete result; no failed segment is silently discarded.

The planned control enumerates two small domains, including zero and a
binding Gupper. Its exact checks cover every actual row and variable bound
of every segment containing each legal positive stock, then compare the
aggregate price at beta=0 and beta=1.7 to full enumeration. The beta=0
DP-attainment path also exercises prefilled unvisited segments without an
extra Native call.

Two narrow additions were communicated before that control:

- Assert finite nonnegative beta in the **parent** price entry as well as
  the inherited child. Otherwise a zero-only or DP-early-exit path can bypass
  the original Oracle's contract. Current intended RMP/test calls already
  supply valid beta; the assertion makes the new entry's contract explicit.
- Reuse the same existing enumeration and child results to check each child
  lower against its own segment minimum, each returned stock's exact S
  membership, and each nonempty child upper against that minimum. A global
  minimum bracket alone could hide a bad nonlimiting segment. These checks
  require no additional Native call or broad requalification.

Prefixing the inherited child reason string with its conditional identity
is also advisable: the complete-domain flag is already correctly false,
but the old reason can retain the words `full_domain`. Final executed
records should not invite that interpretation. Once these small source
adjustments and the concrete control record are available, their review is
sufficient for the proposed same-direction K35 segmentation comparison.

## Executed qualification and K35 research gate

The final reviewed partition implementation has SHA256
`d9e7c23e64dd2a96a5bf5fda58a881345c4ab31e6f34bf2a71b3a99632b90a9e`.
The parent finite/nonnegative-beta assertion, conditional reason strings and
individual segment checks are implemented as requested. The saved
`qualification/segmented_v1/result.json` has SHA256
`3ca124ea7c53254b2e924e9db0ef2ea93ef90288a858d95d1ed9b3fef71a0823`.
It reports PASS. The primary agent reports serial outer charge 0.6828 s;
the reviewer only read the small record and source, without rerunning it.

The two domains contain 49 and 5 true legal stocks. The exact integer
embeddings satisfy 3965 and 188 actual segment-row checks, respectively,
as well as every variable bound and exact positive-S coverage. Four
beta=0/1.7 controls use 12 Native small calls in total. Domain 0 at beta=0
attains the DP bound without a Native call and exercises the unvisited-piece
fallback. At beta=1.7, each of its four segment intervals brackets its own
enumerated value and the complete interval is approximately
`[-6.866678366666668,-6.866666666666666]`.

The second domain includes legal zero and a strong Gupper. Its empty
positive segments remain in the cover with DP lower; known nonempty segments
may have no accepted true stock upper. The complete intervals remain wide:
`[-8,-3]` for beta=0 and
`[-7.915,-1.2166666666666666]` for beta=1.7, both containing the enumerated
full-domain value. These are valid unresolved outcomes, not infeasibility
or closure claims. The per-child records verify exact S membership and
lower/upper direction for each nonempty segment, rather than relying only
on a global minimum that could hide a bad nonlimiting piece.

**ACCEPT_FOR_K35_SEGMENTED_RESEARCH.** The next admitted step is one
same-direction complete price comparison on a preselected saved beta/d,
with four serial 75-second Native allocations and complete outer cost.
Record that direction and its reason for selection before the new call.
The saved full R, original Q identity, ratio/objective coefficients, beta
and every state cost must be identical. Reuse legal warm stocks only after
re-evaluation at that direction. A promising bound-producing choice has
`C_Q+min(a_K,old_price_upper)` above the current accumulated lower; otherwise
even an exact price at that direction cannot improve that lower.

The saved exact Q constant and true-column `a_K` remain valid for repricing
the same direction/domain. Use their exact stored values and compute

`C_Q + min(a_K,L_m)`

once. The maximum of old and new qualified full-domain price lowers is
permitted, as is the minimum of true global candidate uppers. Do not use a
single segment lower, old RMP ObjVal or a restricted-domain upper in this
correction. No old RMP solve is needed for this first comparison.

If that comparison materially tightens the complete price interval at
controlled additional cost, the same qualified parent-oracle interface may
be used for subsequent coupled iterations, retaining all legal columns,
qualified intervals and ordinary primal/certificate checks. No additional
small-domain qualification is requested for that exact interface reuse.
If a weak or unresolved segment dominates, record that pricing limitation
and its actual cost without promoting a conditional result to a full bound.

The source/core identities are unchanged: frozen pricing SHA
`8ed325356a9171a3e1aaafbc4a5c0526a764f0c35148dd6de2ea15d0d925e558`,
frozen common SHA
`7f4138d995e53b53aed39d255048d8f9ca4aeb368e2d1cea1d4821883fda0233`,
and complete-panel matrix SHA
`d81767d4adfe9ec20a2f5bfcc6cd26450773f2f93fe3231459603c523210374e`.
This gate is research-only and does not change the admitted production
candidate, online stopping rules or full-panel identities. Keep all new
Native work serial and preserve the normal completed K35 checkpoint.

## Saved-direction repricing driver review

The reviewer statically inspected `scripts/round153_refine.py`, SHA256
`9db027ad6324995bb5c817105317bf08d54f78485eeb9611cc5710cd03408d5d`,
and the two small source/refinement plans while the admitted price comparison
was running. **ACCEPT_CURRENT_SAVED_DIRECTION_REFINEMENT**; no validity issue
requiring interruption was found. No solver or heavy evidence replay was
started by the reviewer.

The source is `K-35-U_price_deep/iter00003`. Its plan and the refinement plan
have identical scope and Q SHA
`9816772328dd5e53c0dfd00e5f714fbaf08d2f93ac3cf0652ce5226a2452fcb5`.
The registered source certificate SHA is
`274f767ed102cb31159e7f4186b4747a7007fbb322fe6bcaa98325327e323401`
and source price SHA is
`39201e20cddd7f23cab0fba099028ad9dd03b5dc09865c5de3dede534de414cf`.
The pre-call recorded corrected potential is `.28371123456466546`, above
the then-current accumulated lower `.2818261599167829`.

The driver reads `d_exact` as Fractions, checks beta against the certificate,
and checks every price state against the negative saved pi in exact
binary64/Fraction representation. It constructs only the already qualified
PartitionedOracle, checks returned scope/beta/d identity, combines the
same-direction lower by a maximum and reuses the saved exact `lower_exact`
Q constant and `a_true_RMP_exact`. Its final expression is exactly the
previously approved one-convexity correction. It does not optimize a master
or use an RMP objective as a lower. New true legal candidates are merged
with retained stocks, while the previous strengthened-LP upper remains an
upper. Recording a support from the new price alone is conservative even
when the retained old price lower is stronger.

One general interface strengthening was communicated without stopping the
valid current call: the driver automatically checks the resume Q hash, but
does not yet read the source iteration's parent plan to assert the source
Q hash as well. Equal inventory scope alone would not establish equal Q in
a different use of the driver. The present source-Q identity was independently
checked above; no rerun is required. For later use, assert source-plan
Q/scope against resume/reference and record its SHA. An explicit assertion
of returned `complete_domain` will also make the intended parent-oracle
contract clear if the driver is extended.

The current `level_zero_pool` implementation was also checked: it selects
the zero center, includes all true legal pool columns through `Master.add`,
counts only actually fresh columns, separates the fresh negative-RC subset,
and preserves the before/after count. If the saved-direction price comparison
supports continuation, using the same complete parent oracle in that driver
retains the existing gate; record the chosen price engine and partition
alongside the unchanged stabilization/pool mode. Do not route a child
SliceOracle result directly into the master certificate.

## Concrete coupled factory integration

The subsequent `round153_coupled.py` SHA256
`81a4f528a9772b898385e1991e5995642e2ba641302125356f700b5e33fed6fe`
adds `level_zero_pool_bins4`. Static review confirms that it activates
stabilization, level continuation and legal pool insertion together, retains
the zero center, and replaces only the price factory with the qualified
`PartitionedOracle(scope,env,old_joint=old_joint)`. The plan records four
positive-S parts. The Q bounds, primal qualification, exact true-column
`min_K/a_K` and one full-price correction are unchanged. Only the complete
parent price reaches the certificate; no child slice lower is substituted.

**ACCEPT_COUPLED_PARTITION_INTERFACE** under the already stated research
decision: use it when the saved-direction comparison gives material pricing
benefit, then retain all prior columns and intervals in serial continuation.
The source change does not alter the frozen pricing/common modules or the
admitted complete-panel matrix. No additional Native qualification is needed
for this direct reuse of the tested parent interface.

## One 16-slice saved-direction comparison

**ACCEPT_ONE_K35_16_SLICE_COMPARISON.** The reviewer inspected the updated
`round153_refine.py` SHA256
`f288d186de828737e502992cbdf7741dde9597d3bb18618e0029ac8ff05e6531`
and the unchanged partition implementation SHA256
`d9e7c23e64dd2a96a5bf5fda58a881345c4ab31e6f34bf2a71b3a99632b90a9e`.
This is a static gate, with no reviewer Native execution, compilation or
replay. The primary reports that the preceding four-slice comparison cost
277.5028 seconds and produced a weaker global price lower than the saved
monolithic lower. Its latter two slices retained materially wider intervals;
that observation motivates one narrower-denominator comparison, not an
automatic return to partitioned column generation.

The driver now reads the source iteration's parent plan, asserts its Q SHA
and scope equal the resume/reference identity, records that plan's SHA, and
asserts the returned parent price has `complete_domain` together with exactly
the original scope, beta and `d_exact`. It parses `parts` as an integer,
requires `1 <= parts <= 64`, records the chosen count, and passes it directly
to the qualified `PartitionedOracle` constructor. Both prior interface
strengthening points are closed.

For `parts=16`, the exact rational formula
`lo + (hi-lo)*j/parts` gives an exhaustive closed cover with shared endpoints.
The same reciprocal bounds and per-site coefficient-error transportation
remain valid on each narrower interval; the proof and the prior small-domain
qualification do not depend on the number four. The parent still minimizes
over all conditional slice lowers and the separate legal zero state, using
the global hard-total DP lower for any unvisited or unresolved slice. Thus no
extra small-domain Native qualification is required solely for this parameter
change. A total Native cap of 600 seconds becomes 37.5 seconds per slice;
all model construction, DP, serialization and other outer work remain charged
in addition to the Native caps.

The admitted next step is one serial run after the active NC20 research job
has closed, using the same saved `K-35-U_price_deep/iter00003` direction and
the existing Q certificate. Preserve the previous inventory/support lineage
and accumulated interval. Combine price lowers by a maximum before applying
the original exact `C_Q + min(a_K, L_price)` correction once. No RMP re-solve,
change of Q/R, or production change is included in this gate. A weaker new
price must not decrease the retained lower or be described as an improvement.
The earlier condition requiring material pricing benefit before a partitioned
coupled continuation remains in force.

The reviewer rechecked that frozen `round153_pricing.py`,
`round153_common.py`, and `confirmation_matrix.json` retain respectively
the previously admitted SHAs `8ed325356a9171a3e1aaafbc4a5c0526a764f0c35148dd6de2ea15d0d925e558`,
`7f4138d995e53b53aed39d255048d8f9ca4aeb368e2d1cea1d4821883fda0233`,
and `d81767d4adfe9ec20a2f5bfcc6cd26450773f2f93fe3231459603c523210374e`.
