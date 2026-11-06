# Observed Native coefficient omissions in the fixed-level prices

The six-arm complete-algorithm panel closed successfully on
2026-11-06 at 03:51:33 UTC. Its immutable `panel_completion.json` binds all
six eligible arms to actual successful outer receipts; the failed original
position-3 dispatch remains separate. No offline level price is an input to
any complete arm.

The post-panel preparation `prepare_remaining_capacity_queue_v2` passed
and cost 1.3994561000727117 seconds. The first actual child,
`K35_level_v2_readback_v1`, failed at the exact dynamic-row comparison for
`hard_cost_D_definition`, costing 3.7558556001167744 seconds. The queue
stopped with `completed=[]`. None of its remaining audits, support replays
or substantive continuations ran. Both the failed fee and source snapshot
are retained; that label must never be reused.

The metered `level_price_matrix_diagnostic_v1` examined all 19 actual
fixed-level-v2 prices (18 K35, one NC20), without Optimize or Native model
reads. All had Native-omitted state-cost coefficients; the 608 row-entry
differences were omissions with maximum absolute coefficient
7.589415207398531e-19. The same state coefficient is omitted consistently
from the D definition, W definition and both residual epigraph rows.
This diagnostic cost 0.7737317001447082 seconds and is not a qualification.

The subsequent `level_price_omission_assessment_v1` cost
12.00169870001264 seconds. It retained the original numerical guard and
separately bounded the observed coefficient transport error. If the actual
Native state costs are a_iy, the exact intended centered costs divided by
scale are b_iy, and S <= u, the additional scaled residual upper error is

    epsilon = u * sum_i max(0, max_y(a_iy - b_iy)).

Thus the safe recovered residual lower uses
`scale * (Native_bound - original_guard - epsilon)`, followed by the
unchanged signed positive-denominator conversion and separate zero branch.
No part of the existing numerical guard is silently spent twice.

The assessment also independently ran the hard-total unary DP on the
actual Native costs. All 19 actual cost minima/maxima lie within the saved
D bounds. Consequently, the D/W definitions and four saved outward
McCormick rows still admit every legal inventory when evaluated with the
actual costs. This establishes the relevant domain property for these
omissions; small coefficient magnitude alone would not establish it.

The largest additional scaled residual error is 8.950292221775181e-17.
Seven K35 prices have recorded lower values one binary64 step above the
new conservative recovered value: iterations 0, 1, 4, 10, 11, 13 and 15.
The corresponding seven saved support RHS values also need correction.
The other 12 prices/support rows pass this particular comparison; the NC20
omission has zero one-sided residual upper error. These facts do not yet
constitute the complete price/Q/model/selector readback.

The raw prices, supports, phase results and failed checks remain immutable.
Before resuming substantive continuations, create explicitly linked
qualified corrections, recheck the saved matrices and full certificates,
and use the corrected cumulative supports in the free-Q replay. The
forward Round155 bound interface must account for actual Native omissions
as well. Preserve the inherited oracle/domain, true prices, original Q,
numerical policy and the single selected level strategy. This is a repair
of the observed certificate transport, not grounds to accept near-equality
without a bound or to rerun the completed physical panel.

## Executed repair and readbacks, 2026-11-06

The historical diagnosis above is retained. The repair is now implemented
in round155_price_certificate.py and the forward oracle wrapper. Actual D
coefficients are recovered from the saved Native matrix, with strict
consistency checks for W, both residual epigraph rows and all four product
rows. Actual-cost extrema are checked against the saved D bounds before
accepting the bound. The additional one-sided error is subtracted in
addition to the full original numerical guard. No optimization model,
integer domain, target, zero case or signed-denominator rule was relaxed.

The actual interfaces_v5 tests exercise omitted tiny state costs by full
small-domain enumeration on both oracle paths. loop_admission_v5 binds
the current source hashes. The metered constructor
price_transport_requalification_v1 (14.424786200048402s) wrote derived
price and phase records linked to the unchanged raw sources. The corrected
K phase SHA is4220c022f9157371ccb122fad53d87ca55985019650bfedc3bb781ea4f9b2509;
NC is797a68dfdba8d0fe92af71529ff38cb5cc305be799b84399c94c1ad7fdd388d8.
Seven K price lowers and support RHS values decreased by one binary64
step. NC's derived bound values are unchanged. Neither domain's retained
whole-hull interval, feasible inventory columns or upper witness changed.

The separate general readers independently derived actual coefficients,
cost extrema, transport error and recovered prices, and rechecked original
Q residuals, true columns, sparse primals and actual model reconstruction.
K35_level_v2_readback_v2 passed (18 prices,47.25549310003407s);
NC20_level_v2_readback_v1 passed (one price,21.746189499972388s).
Both actual selector readbacks passed, including every saved candidate,
full current-column minima, fixed-level chronology and unresolved exits:
K35_level_v2_selector_readback_v1 cost154.36812680005096s;
NC20_level_v2_selector_readback_v1 cost56.38562840013765s.

Both complete corrected-support replays and their separate original-Q
matrix/dual/primal readbacks also passed. K's replay/readback cost
8.408092200057581/5.587604200001806s; NC's cost
5.935161300003529/3.811372499912977s. These replays are actual new LP
optimizations and are not labelled as constructor-only derivations.
Their full-hull intervals remain unchanged; a support-LP primal objective
is still not a full-hull upper.

review/remaining_readback_bindings.json is the later, hash-bound actual
admission. The constructor's original INDEPENDENT_READBACK_REQUIRED index
and all failed receipts remain immutable. The v3 serial continuation plan
starts from each domain's own corrected and replayed support set. These
passed checks admit the remaining substantive opportunity; they do not
establish research saturation or complete the user goal.
