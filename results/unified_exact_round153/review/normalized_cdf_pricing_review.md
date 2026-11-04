# Normalized CDF price strengthening: independent review

Decision: **ACCEPT_FOR_TARGETED_IMPLEMENTATION_QUALIFICATION**. The proposed
rows are valid necessary inequalities for the existing complete positive
inventory price domain. They reuse the historical CDF/OT absolute-difference
construction under a common normalization factor; they are not a new Gini
identity or a complete resource-constrained inventory hull. The current
price source does not contain this normalized-w block. Review was limited
to mathematical reasoning, source reads and small historical Markdown reads
through Git. No solver, enumeration, compilation, archive download or large
historical evidence replay was performed.

## Exact formula and extension

For a station pair i,j, form exact ratios `rho_i(y)=Fraction(c_i)*y` from
the actual binary64 c coefficients and integer supports. Sort the union of
the two supports and zero as `q_0 < ... < q_K`. Use
`delta_k=q_(k+1)-q_k` and `W_i(k)=sum_{rho_i(y)>q_k} w_iy` for
`k=0,...,K-1`. Including the final breakpoint without a following interval
must not add an extra width. Repeated exact values are merged; different
state variables remain distinct.

At an integer selector in the positive branch, `w_iy=t*x_iy` and
`W_i(k)=t*1[rho_i(Y_i)>q_k]`. Consequently

`sum_k delta_k*abs(W_i(k)-W_j(k)) = t*abs(rho_i(Y_i)-rho_j(Y_j))`.

Summing over all station pairs gives nG. If the new epigraph variables only
satisfy `a_ijk >= +/- (W_i(k)-W_j(k))`, their aggregate D is generally **at
least** nG in the exact-coefficient formulation. Equality holds for the
constructive extension `a_ijk=abs(W_i(k)-W_j(k))`; it is not imposed on every
feasible auxiliary assignment. This extension proves `D<=n*q` and
`D<=n*gamma_U` valid because q may be any completion at least true G and at
least gamma_L. In particular nonminimal completion is not excluded.

The zero-stock state remains the existing separate branch. No reciprocal
or CDF positive-branch extension is applied to S=0. The new a variables and
their constraints do not alter the old mean-difference variables, NC/TS
rows, original selector supports, hard totals, objective or full Q.

## Bounds, rounding and continuous strength

The station mass rows imply `0<=W_i(k)<=t`. Thus the minimal auxiliary
assignment satisfies `0<=a_ijk<=t<=t_U`. Using the existing actual outward
t_U as the finite variable UB is safe. A row `a_ijk<=t` would also preserve
the projected CDF formulation, provided these new variables occur only in
their absolute-value epigraph and nonnegative aggregate upper-bound rows:
replacing them by their minima can only help those rows. An upper of one
is not safe in general, because t can exceed one. Do not transfer this
decrease argument to old absolute-value variables that also participate in
other lower-bound rows.

For the submitted all-a version each positive exact delta occurs once on
its own nonnegative variable. Rounding that coefficient down weakens the
added upper-bound rows and preserves every constructive integer extension.
Use an upward RHS for `n*gamma_U`; the integer coefficient n in the q row
is exact. With downward widths the loaded aggregate need not equal nG,
which is another reason to retain the original mean-absolute/Gini rows.
The objective coefficients and original-unit price transport remain
unchanged, so the existing beta/d scaling and guard contract is retained;
this is the same declared numerical Native policy, not a rational Native
certificate claim.

At a continuous point with equal station masses, the exact CDF expression
dominates the corresponding mean absolute difference by
`abs(sum_k delta_k*(W_i-W_j)) <= sum_k delta_k*abs(W_i-W_j)`.
Strictness is possible. For example, with two stations, c=1, supports
{0,1,2}, hard totals [0,4], gamma_L=0 and gamma_U=1/2, take t=1/2,
station-one x=(1/2,0,1/2), station-two x=(0,1,0), and w=t*x. Both normalized
means are 1/2, so the old pair absolute variable and q can be zero. Both
NC aggregates are zero on this full hard-total scope, and the existing TS
rows with t bounds [1/4,1] hold. The two threshold differences have magnitude
1/4 each, giving D=1/2 and requiring q>=1/4. This is an exact point-level
strictness illustration for the pricing blocks, not a measured real-role
objective gain or a routing/full-Q witness.

Conversely, identical fractional CDFs can give D=0 while hard-resource count
rows are positive (for example identical half-masses on {0,1} with exactly
two units across four stations). The CDF block does not dominate NC in
general. Retaining NC/TS is necessary; observed benefit remains an empirical
question for the saved price direction. Downward rounding also means exact
dominance of the loaded CDF row over the loaded mean row should not be
asserted without accounting for rounding; the retained union is sufficient.

Do not introduce threshold compression in this first qualification. If it
is later used, a constant zero or t tail can be replaced by a nonnegative
sum of w variables using the mass equality. Accumulate repeated coefficients
exactly before downward conversion; separately rounded widths added in
binary64 need not preserve a final downward rounding relation. Expressions
with negative coefficients need the established signed transport instead.

## Historical identity and retained negative evidence

`scripts/round88_ot_math.py::pair_cut` already constructs signed CDF pair
rows. `scripts/round88_ot_epigraph.py::make_plan` constructs the complete
B1 pairwise absolute-CDF epigraph on every merged ratio interval. Replacing
unit-mass state marginals by the equal-mass w marginals and aggregating the
normalized pair costs is the present common-t reuse. The historical source
SHAs inspected here are respectively
`2b8855609cf469098d050fcd9c89efac01b2cb41ee07f023b5a7b79f9ff71840`
and `5d49c3fc12cc806a8008e43d756bf9c46810b21e7efc2b64c2383da4624bd7da`.
Use exact products of the actual c coefficients and y, not a nominal target
ratio or an uncorrected rounded product; the later historical native-B1
contract specifically corrected that distinction.

Fixed historical references were read directly from these commits:

- `247cf16b89e4a6c47b157d6eee1f981c7e8c9b98`,
  `results/unified_exact_round88/ot_epigraph_decision.md` and
  `ot_epigraph_diagnostic_report.md`: the F2 B1/B2 fixed LPs completed at
  essentially the same numerical objective, with B2 larger and slower;
  four D7 fixed-LP arms hit their whole 300-second limits without completed
  qualified objectives. They were not complete-method performance arms,
  and their unfinished values must remain unknown.
- `cce067956156b505652110f5dde6839c3af8c4e1`,
  `results/unified_exact_round88/native_ot_b1_contract_review.md`: actual
  model-link products, rather than nominal target ratios, govern valid
  finite-support coefficient construction.
- `fe19ca9d519d5c60e4b7bf37085645b41ae44723`,
  `results/unified_exact_round89/native_b1_decision.md` and
  `runner_native_b1_g3_rest_stop_independent_review.md`: both D3 complete
  arms certified the same original objective, but ENS-C took 155.391 seconds
  versus native B1's 299.828 seconds, with terminal Work about 216.499 versus
  429.367. That native callback candidate was parked and ten unstarted arms
  remained unrun. This is a strong single-pair negative signal, not universal
  CDF invalidity and not an isolated causal estimate of the rows apart from
  PreCrush/search-path changes.

The present price-only normalized block is a different use of that old
mathematics. These negative/censored records must remain visible, while a
small targeted pricing comparison is justified by the newly observed full
price uncertainty. No R89 production restart or broad OT campaign is admitted.

## Concrete source and minimal qualification gate

Inspected `round153_transport.py` SHA256
`0ef3465b2c5bde7d7fb085ba5bff73bc6cc15862cec1f4a07d107e9a9fd32ae6`.
It adds only continuous nonnegative td variables with UB equal to existing
t_U; exact merged support intervals; the two +/- tail rows per interval;
and the downward-width aggregate q/cap rows. It retains the original model
and updates its structural snapshot. A copied function namespace changes
only the writer metadata; stock validation, full price objective, guard,
accepted statuses and zero handling are unchanged. The constructor safely
handles a missing positive-branch model. No static validity blocker was
found. The frozen core pricing SHA remains
`8ed325356a9171a3e1aaafbc4a5c0526a764f0c35148dd6de2ea15d0d925e558`.

The submitted qualifier extends every positive legal stock in the existing
49-stock and zero/tight-G-cap domains, verifies the exact nG identity, then
checks every actual variable bound and every actual model row with Fraction
arithmetic. Its beta 0/1.7 signed-cost controls compare the complete price
bracket with full stock enumeration. This is an appropriate finite gate.
The first domain's beta-zero control can exit at the exact DP fallback;
the second domain's tight G cap is intended to force a real beta-zero Native
call. Confirm an actual call in that control, together with a positive-beta
Native call, before marking objective/cap integration qualified. Preserve
all call/model/return and extra-column/row counts. Small-domain qualification
does not demonstrate real-role speed or complete-hull value improvement.

After those controls pass, one previously saved, exactly bound direction
may be compared at the existing full-price allowance, using all legal warm
stocks, the same Q/scope/direction and the original once-only correction.
Record full construction and solve cost, model-size increase, price interval
and actual useful bound increment. Retain the best previous valid price
lower and true candidate upper. A switch of the continuing coupled loop is
conditional on useful evidence; it is not authorized by the identity alone.
All new work is serial and metered, with frozen production files unchanged.

## Qualification receipt and two saved-direction gates

**ACCEPT_TWO_TRANSPORT_SAVED_DIRECTION_PROBES.** The reviewer read the small
`qualification/transport_v1/result.json`, SHA256
`ea529ea32e714c608619e0fcd89088570599b65704d8fe93480b84b34827e89e`,
and the closed `transport_interface_control_v1` outer receipt. Exit was zero
and the charged outer duration was 0.38825779990293086 seconds. No control
was rerun by the reviewer.

The first domain reports exact identity/actual-row verification for all
49 legal positive stocks and 4949 rows; the second for its four positive
stocks and 228 rows, with legal zero handled separately. The four signed-cost
beta controls contain three actual Native calls. In particular the tight-G
domain's beta-zero and beta-1.7 return files both record an actual Status 2
return. The beta-zero exact price -3 is inside [-3.5000090000000004,-1.5];
the positive-beta exact price is also inside the saved wider bracket. These
are honest unresolved true-price intervals under the inherited numerical
policy, not complete-price optimality inferred from Native's OPTIMAL status.
The first domain's beta-zero exact-DP early exit remains separately identified.

The qualified extension source SHA is now
`8d2ed07b61d6cdd9cf9189ce817ea819144e77857010b03339851936a209d058`.
Static inspection confirms the same constructor arithmetic, with added
metadata explicitly crediting R88 and disclaiming new general Gini theory.
The refinement driver SHA256
`cb34ecedbce53552988beee3d14a97a6db175b91315904fa76b589ca7fda059c`
adds `implementation='transport'` by replacing only the Oracle factory. It
records that implementation and `positive_S_parts=None`; the existing
source-plan/certificate/price hashes, Q/scope/beta/exact-d equality checks,
complete-domain result assertion and once-only C_Q/a_K correction remain.
All returned legal stocks and the previous bounds/supports are retained.

The admitted finite comparisons are:

- N-C20-U: saved `N-C20-U_level_zero_continued/iter00008`, Native cap 120
  seconds. The inspected completed iteration is not Phase I, has a qualified
  numerical RMP primal, and retains the old full-price interval
  [-0.000049866664940572364,0.00726560247528965]. The primary's pre-comparison
  selection rule is the largest prospective corrected lower based on a true
  inventory-price upper, about .18354007. It is a direction-selection
  heuristic, never a new lower by itself.
- K-35-U: the unchanged saved `K-35-U_price_deep/iter00003` direction, Native
  cap 300 seconds. Preserve the earlier monolithic, partition and overlay
  outcomes and their costs.

The N-C20 source plan SHA is
`6745a12c17b4aa52374b761d607524bb93a296c87a3a84a0c306ce109b0400a7`,
certificate SHA is
`d0c856bae71a02db925ca498230d5b66ea2d73e4994c5c99f3462157d9b69e94`,
and source price SHA is
`67b1a91469d5af7f156213266f607e892c6af2600cbb40ef4e62c64b569a31f7`.
Its Q SHA remains
`fefd769b819d36a93dfaa8dc39670512109323cdd0123366e768443cdf2a1d45`.

Run the two comparisons serially and charge construction/readback/output
overhead as well as search. An inferior new price cannot reduce the retained
lower. A beneficial result can motivate a separately checked coupled factory
adaptation; this gate itself changes neither coupled execution nor frozen
production. The longer K35 monolithic comparison may be deferred while these
cheaper probes answer the pricing question; no production identity may be
selected from full-method outcomes. Frozen pricing/common/confirmation-matrix
SHAs were rechecked unchanged.
