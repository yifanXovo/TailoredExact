# Independent review of targeted residual strengthening

Reviewer: `/root/review_round154`, independent of the implementation.
Disposition: **ACCEPT_TARGETED_STRENGTHENING** at the source/qualification
identities below. The first failed qualification is retained and the
actual identified defect is repaired. This review does not establish
performance superiority or admit an automatic new variant matrix.

The reviewer read round154_strengthened.py, the modified exact-extension
qualification, the failed outer stderr/receipt, the successful v2 summary,
representative actual MPS/strengthening metadata and the narrow real-price
driver change. No solver, Native model load, enumeration, compile or
performance process was started by the reviewer.

## Mathematical purpose and conditional denominator rows

The initial60-second screens show weak residual LP/MIP proof progress on
the same signed target tasks. The next change specifically retains two
pieces of finite hard-total information: conditional S ranges for each
state/complement, and hard-total DP cost bounds missing from the basic
state-product LP. This follows the explicit C3 limitation rather than
renaming an old general formulation. It introduces no partition, CDF,
flow, pool grid, changed support or instance-dependent rule.

For a supported state k=(i,y), a safe conditional interval [l1,u1] on
S when x_k=1 gives l1*x_k<=z_k<=u1*x_k. A safe interval [l0,u0] when
x_k=0 gives l0*(1-x_k)<=S-z_k<=u0*(1-x_k).
At an integer state, z_k=S*x_k, so both pairs are valid and preserve
every original legal positive inventory.

The denominator helper optimizes a resource-constrained support box;
holes only expand that bounding box. Consequently its extrema still
bound every original conditional stock. The new code intersects them
with the already qualified global positive [l,u], rounds outward and
uses no Gupper-based exclusion. An actually resource-infeasible conditional
box, or hi<lo for the positive branch, may fix the binary away from that
condition. It does not justify deleting a legal zero branch: zero stays
outside this entire positive model.

## Actual qualification failure and repair

The first version interpreted denominator()['applicable']==False as
an empty conditional domain. The inherited helper also returns that flag
when S_L=0 and S_U is positive. A conditional scope may contain both zero
and valid positive inventories, so this interpretation wrongly fixed a
state binary to zero. The actual finite extension check caught
AssertionError ('x[1,0]','UB') before any large use of that version.

The repaired code checks for the S_U_exact field to distinguish the
helper's infeasible-box return, then computes
max(global_l,S_L)<=S<=min(global_u,S_U). A zero lower endpoint therefore
uses the qualified positive global l while retaining possible positive
stocks. Only an absent feasible bound record or a genuinely empty
positive interval fixes the state/complement. The code and mixed-zero
actual-row qualification close the observed defect.

The failed receipt has exit1 and .5064127999357879 outer seconds, no
timeout/supervisor failure. It remains a paid failed attempt, not PASS or
a negative model performance result. The corrected v2 receipt has exit0
and1.0460245001595467 outer seconds. Neither is overwritten or free.

## Signed cost DP and four product rows

The implementation computes exactly the same scale, station anchors and
downward binary64 centered-cost coefficients t_k used by the residual
core, then asserts the saved core call's coefficients/scale match.
Define Dhat=sum t_k*x_k and What=sum t_k*z_k. These are written equalities
over the actual binary64 t_k, with both variables free as needed.

Hard-total exact Fraction DP on t and -t gives safe outward endpoints
a<=Dhat<=b. They are bounds for this written centered/scaled cost, not an
incorrect substitution of true unscaled d bounds into another product.
At an integer inventory What=S*Dhat. The four added rows are

    What-l*Dhat-a*S >= -l*a,
    What-u*Dhat-b*S >= -u*b,
    What-u*Dhat-a*S <= -u*a,
    What-l*Dhat-b*S <= -l*b.

The coefficients l,u,a,b are the actual binary64 values and their scalar
RHS products are computed with Fraction and rounded down for >=, up for <=.
Thus all signs are safe even when the tight costs are negative.
The actual MPS contains those four rows, the Dhat/What definitions,
safe Dhat bounds and free What. A representative v2 model has31
variables,9 binaries,104 rows and319 nonzeros.

These rows are valid extra consequences of the same original inventory
domain. They supply exactly the kind of DP-tight aggregate information
that the Cartesian state-product theorem does not automatically imply.
The unchanged epigraph remains intentionally downward relative to true
residual; adding valid rows on the written cost does not reverse that
lower-bound direction. The new model therefore remains a necessary
integer extension and retains the old safe conversion/zero/DP/inherited
composition. It is not a normalized-RN dominance result.

The qualifier extends every exact true inventory point with
Dhat equal to the sum of actual saved written coefficients and
What=S*Dhat, then checks every row and bound with Fraction. It does not
fill those new variables with original unscaled costs. The successful
strong-v2 pass includes mixed signed/nonzero state rounding, beta0,
both target signs, mixed/zero-only branch, nonminimal A, inherited lower,
parameter transport, and all new actual rows/bounds.

## Real-price driver and interpretation

The driver adds only residual_strong selection, checks the successful
strong-v2 source hash and otherwise uses the same frozen K35 direction,
initial stocks, tau, original-price summary and outer-cost rule.
The already repaired fresh-versus-inherited separation remains.
Its original C_Q/a_K/target ceiling stays unchanged.

A60-second targeted stronger screen is a reasonable finite check of the
observed weak product relaxation. It cannot by itself settle whether
the residual route improves useful proof cost; one documented substantial
proof opportunity remains appropriate for a useful surviving direction.
A stronger LP can still produce worse finite MIP progress, so the
actual raw result rather than the word strengthening determines the
performance conclusion.

The conditional_construct_seconds field starts before the base
constructor, and therefore includes base model construction. This is
a nested timing observation, not a pure conditional incremental cost.
The parent acknowledged that final accounting uses unique outer elapsed
receipts and does not sum this field again with base construction.
The reporting distinction closes the only identified cost-label issue.

## Bindings

- round154_strengthened.py:
  670d385ef6f9239b705fea92345709d4d4edbfe17dd732bb95b76b9b18460824.
- Unchanged round154_residual.py:
  04bfa84774b7be4603ec08ae88ba015d6351d2bd3109a1d599fd4709f18bbc50.
- Extended round154_qualify.py:
  7141800381ef63a8d90396e6fc7611cdc7c7929afe7c7825eb07033b46d3e95b.
- qualification/strong_residual_v2/result.json:
  94ab47cb42d774d956f4e9a25a6677e7464a104037f63dd455f12255abee39c7.
- Representative fixture2_beta1.7_target1/model.mps:
  60d03a80298aaab89cb1e972a49157ac0f70bcac0a0768c554ed971d8684cc63.
- round154_targets.py with residual_strong selector:
  e14d09042e62a0f4b3082228f18eb3d69c2af0c4d75bbe9074c446e5697196e8.

This source review and finite qualification do not alter the independent
E complete-panel admission or its frozen execution chain.

