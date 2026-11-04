# Independent coupled-interface review

Reviewer: `/root/independent_review`, 2026-11-04 (Asia/Shanghai).

Verdict: **ACCEPT_FOR_THREE_DOMAIN_RESEARCH**, for both default pricing and
the optional old-joint pricing relaxation. The design gates are closed for
the reviewed implementation and targeted qualification. N-B35's initial
coupled window, the other two domain intervals, and evidence-directed
deepening may proceed within the serial budget. This gate does not approve
a production candidate or claim a complete-algorithm benefit.

The reviewer read the concrete sources, saved qualification results and
selected Native call returns/logs. No new Optimize, Native load, compiler,
checker or performance experiment was run by the reviewer. All qualification
and C3 computations were launched by the primary agent through the serial
Round153 outer meter. This report adds source review and writing only.

## Reviewed identity

| File | SHA256 |
|---|---|
| `scripts/round153_coupled.py` | `2dbb70171acbb14af70e2fb2c4263ddb595464b0e0a1ddacf66714204a722651` |
| `scripts/round153_pricing.py` | `e0398c163f30146074077d1557fe1ec2dd2f811c628c87c6aefbaeabd84e1094` |
| `scripts/round153_lp.py` | `18280fe215da42838e8e04f1a4cee6ee611685e734d3de31667559f2fb468340` |
| `scripts/round153_qualify.py` | `b3c2a48d05b1012a2dbea8933576adfaffe0356087eb2a003f204b7e4310d26` |

The earlier [design review](design_review.md) supplies the mathematical
derivation and scope. This report records the concrete interface checks and
the issue found during implementation review.

## Full-Q dual certificate

`Master` derives missing finite bounds from the complete Q before adding any
lambda column, link, Gini margin or artificial variable. The certificate
explicitly passes those Q bounds and excludes all lambda columns. Thus no
bound implied only by the restricted column set enters the all-column lower.
All original-Q row multipliers and original-column residuals still contribute,
with sign repair and exact Fraction arithmetic on actual binary64 values.

The written marginal row is `sum(lambda*v)-s=0`, so its Native multiplier is
the goal's pi directly. The convexity multiplier is a and the nonnegative
Gini-row multiplier is beta. These signs give `beta*f-pi*v-a` and match the
saved negative-reduced-cost test.

The RMP uses upward-rounded f and an additional 1e-8 primal Gini margin.
`certificate` excludes both the convexity RHS and that Gini-margin RHS from
its Q-supported constant. Its restricted intercept is

`a_K=min(a_raw,min_{Y in K}(beta*f(Y)-pi*v(Y)))`,

using true Fraction f, not its written upward-rounded coefficient. Therefore
`D_K=C_Q+a_K` is a qualified restricted dual lower for the intended true hull.
The subsequent `delta=max(0,a_K-Lm)` is applied once. The resulting lower is
`C_Q+min(a_K,Lm)`. The original Q lower can safely tighten it by taking a maximum.
The primal margin is not claimed as a valid row of the research target.

`support_row` preserves beta's scale, including zero and tiny beta. Its RHS
transport adds the minimum finite-G coefficient error and each station's
minimum selector-coefficient error. This matches the goal's transport formula
after changing the sign of pi. There is no division by beta.

## Primal upper and Phase I

The upper check covers every current Q/RMP row and bound, lambda mass and
negative mass, all marginal coordinates (including the omitted one per
station), and the true Fraction-weighted f completion. An accepted RMP value
is explicitly labelled an upper on the strengthened LP value, not a physical
BRP incumbent and not a BRP lower bound.

This remains the inherited **numerical primal feasibility qualification**:
small lambda and link residuals are allowed, and the source/result explicitly
say it is not a rational primal certificate. The 1e-8 Gini margin protects
true completion in the observed fixtures. Reports must retain the actual
residual envelope and that numerical identity; any numerical crossing of
lower and primal values should be disclosed rather than treated as an exact
negative gap. No historical primal experiment is reopened by this review.

Phase I sets every original and lambda objective coefficient to zero, adds
signed link artificials and a nonnegative Gini artificial, and minimizes their
sum. The revised code also saves/zeros/restores ObjCon, so the zero-artificial
test is not confused by an original objective constant. It removes artificials
and restores the original objective before accepting an ordinary upper.
The saved missing-column fixture has restricted infeasibility, positive Phase I
objective 1.5, zero artificial objective after adding legal columns, and a
qualified normal upper. No full-hull infeasibility is inferred from the initial
RMP. Original x is fixed only in that explicitly labelled small qualification
fixture, never in the real complete-LP comparisons.

The run now initializes a durable undecided result before the first iteration,
records the exit phase and columns, and writes a basis only after an optimal
LP status. Thus an early budget/Phase-I checkpoint does not require an undefined
normal-result object. This is a bookkeeping fix, not a new scientific result.

## Generalized full-domain pricing

The objective is exactly the new interface `beta*f+sum d`; unary h is added
only by a caller that intentionally supplies the floor costs. The hard-total
DP lower is `beta*gamma_L+min sum d`. A legal zero state contributes the same
formula at zero, and the positive RN formulation retains all supported states,
hard resources and physical Gupper even at beta=0.

Per-station constant centering preserves the objective by one-hot identities.
The positive power-of-two scaling is undone using exact arithmetic. The
objective conversion correction covers each station's maximum upward written
cost error and the q coefficient error over its finite range. The numerical
guard includes the actual scaled beta and scaled costs and is multiplied back
by the scale; it is not the old unit-q guard copied unchanged. True inventory
candidates are independently recomputed from their integer coordinates before
being used as price uppers or added as columns. Invalid Native candidates do
not become true-stock witnesses.

The optional NC coefficients are rounded downward on nonnegative w/t, which
weakens their RHS safely. The initial TS implementation had a real missing
transport: multiplying the expression `total=sum y*x` by a binary64 reciprocal
slope introduces selector coefficient errors. RHS-only outward rounding does
not cover those errors. This was reported before old-joint research and fixed.
The revised code explicitly forms each actual selector coefficient, computes
its difference from `-Fraction(slope)*y`, and adds per-station minimum errors
for a lower inequality or maximum errors for an upper inequality to the RHS.
It saves this proof as `joint_transport`. The sign and one-hot support formula
are correct; no state or legitimate inventory is removed by this transport.

## Observed targeted qualification

The saved evidence was read, not rerun:

| Record | Result and scope |
|---|---|
| `qualification/v1/result.json` | PASS: 49-column control; correct restricted upper and corrected lower directions; negative reduced cost; true-f/direct-support checks; missing-column Phase I; signed costs, zero and nonminimal completion. |
| `qualification/joint_transport_v2/result.json` | PASS: all 2989 actual binary64 constraint checks over 49 legal inventories, plus the true-price bracket after the TS fix. |
| `qualification/native_beta_v1/result.json` | PASS: beta 0, 2.5 and 32 each make a Native call because the DP witness violates Gupper; all true enumerated prices lie in the saved brackets. |
| `review/exact_strict_example.json` | PASS: independent stdlib-only 169-row/68-bound C3 reconstruction, exact fixed-marginal gap 41/1080; parent-metered and not rerun. |

The first beta fixtures used exact DP early exit. The additional Native-beta
fixture closes that specific coverage omission rather than repeating all old
tests. Its beta=0 and beta=2.5 Native runs return OPTIMAL but still have broad
true-price intervals; this is correctly retained as unresolved pricing, not
mislabelled exact price resolution. The beta=32 original-scale guard is 6.9e-5,
illustrating why Native optimality alone cannot meet every requested hull
accuracy. Future numerical limits should be reported and interpreted against
the scientific increment scale.

The three qualification-result hashes are respectively
`b5357d52de893621d5980033f9b0976e2bc7fc229608edf4097fb7b1ccb8161c`,
`b60ef2d1720585ff778fc2b1cbaca5770a8c8739c826c4ac47f5eeb866a762a6`,
and `a19b91d69e274e5382ccffe06116554b8b7a90387b27bfd07444a9fac0538e54`.

## Remaining scientific obligations

There are no open implementation-validity blockers for the declared three-domain
research gate. A local lack of new negative columns, a Native OPTIMAL price
with a broad true bracket, or a local wall cap remains an unresolved checkpoint.
It is not by itself a negative statement about the whole hull. Important wide
intervals still require the goal's targeted deepening and a quantitative stopping
decision. Final supports must also be freely reoptimized in the same Q, with
projection and Gini-completion attribution kept distinct.

Reference construction and the pure-B floor screen are separate decisions;
neither an RN diagnostic gain nor the new K35 inventory floor bracket alone
establishes a complete-method benefit. Production, if entered, still requires
its separate uniform-rule, own-H, current-domain, Native/Start/scope and complete
cost qualifications. Final evidence/publication review remains pending.
