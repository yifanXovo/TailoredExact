# Independent pre-implementation mathematical review

Reviewer: `/root/independent_review`, different from the primary implementer.
Review date: 2026-10-29 (Asia/Shanghai). This review used ordinary source/blob
reads and exact Python `Fraction` arithmetic. It performed zero Optimize calls,
zero solver imports and zero native library loads. No production file changed.

## Sources actually read

- Round138 goal B and H; `WORKSPACE_POLICY.md`.
- R132 `joint_structure_note.md`.
- R133 `joint_objective_gap_note.md`, read with `git show HEAD:path`.
- R134 `tc_note.md`, `scripts/round134_count_bound.py`, and
  `scripts/round133_joint_check.py`.
- R135 `ap_math_and_history.md`.
- Both historical GS `final_report.md` files under
  `gf_tailored_bc_structural_cut_round` and
  `gf_tailored_bc_structural_policy_round`, read from actual Git blobs.
- The actual saved J2/J3 matrices from the R132 carrier at pin
  `52b02252ba47e8228b73e071d6ed692385a4f816`, SHA256
  `d2e55d7ae5fcaf5bb0c9d39a489b589006f3a29eb350b167fd790ad399a0aac1`.
- The saved R134 exact tiny points in member
  `results/unified_exact_round134/math/tiny_exact.json` of
  `math_failures_and_costs.zip`, whose actual SHA256 is
  `9ef0dfada8b3ed06f5a0c7011e0c20b439a494823186c38bfbb28946ebe2a1a4`.

## Findings

1. The four proposed inventory RLT inequalities have the correct directions.
   Apply each nonnegative factor `g-alpha` and `beta-g` to each of
   `tau-Bminus >= 0` and `B-tau >= 0`, and replace `g*tau` by `J`.
   Stocks exclude the depot. Loaded return gives
   `tau=B-sum(return_load)`, so `Bminus=max(0,B-sum Q)` is valid without an
   equality `tau=B`. No cumulative-pickup bound is needed. The equations use
   inventory products `Z_i=g*Y_i`, without dividing by targets. Heterogeneous
   targets, weights and capacities do not alter this derivation.

2. The continuous-resource-block convex hull statement is correct when every
   defining resource inequality of the stated P has both products, the original
   P is retained, and all per-station simplex/product rows are retained. The
   endpoint decompositions in B3 prove sufficiency. At `g=alpha`, the
   nonnegative differences `q-alpha*s` sum to zero within each station, hence
   vanish; the beta endpoint is analogous. At `alpha=beta`, the bounds already
   force `q=alpha*s`. This is a standard common-factor/disjunctive/RLT result.
   With only the two stock bounds it is the hull of that continuous stock
   product block; it is not the integer-inventory, route or objective hull.

3. For the fixed J2/J3 reference, TC and stock RLT are strictly complementary
   in objective strength. TC gives `Hsum >= a+4*b2 >= tau`, while the existing
   Gini row and the new `J<=3*g` give `Hsum<=12*g`. With `P>=4-tau`,
   `F>=tau/12+lambda*(4-tau)>=min(4*lambda,1/4+lambda)`.
   The original loaded coefficient is exactly
   `5404319552844595/36028797018963968 > 1/12`. The old zero-g balanced
   witness satisfies all stock RLT rows. The TC-only witness has
   `g=3/16, J=3/4`, and violates `J<=3*g` by `3/16`.

   The TC-only value `lambda_hat+3/16` is supported by the retained state
   penalty and old R134 proof; its general-lambda extension is not asserted.
   The four cells at the stated lambda/reference are respectively
   `lambda_hat`, `lambda_hat`, `lambda_hat+3/16`, and `lambda_hat+1/4`.

4. I independently checked a matching complete auxiliary extension for the
   fourth cell. Start from each saved R134 TC witness, retain its four balanced
   true-fleet columns and all service/route/theta/rank/cutset coordinates, set
   `G=1/4`, and add `state_g_i_0=1/16` for each station. Its existing
   `state_g_i_1=3/16`, `zprod_i=3/16`, `h_i_j=1/2`, `Y_i=r_i=3/4`, and
   `e_i=1/4` remain valid. Exact replay using the existing `row_check` returned:

   | Case | Actual rows | Variable bounds | Equality residuals | Violations |
   |---|---:|---:|---:|---:|
   | J2 | 583 | 284 | 0 | 0 |
   | J3 | 583 | 298 | 0 | 0 |

   The retained old state penalty is tight. The existing `old_extensions`
   routine also checked the declared R88 B1 (38 rows) and B2 (70 rows) exact
   algebraic extensions with zero failures. Their q-CDF prefixes now use
   `1/16` and `1/4`; these coordinates were not fixed to the old values.
   For this witness `tau=3, J=3/4, g=1/4`; the four stock inequalities have
   lower right sides `0,3/4` and upper right sides `9/4,3/4`.
   This establishes exact primal attainability on the declared complete
   reference, combined with the analytic lower bound; it is not a new native
   sensitivity experiment. No unchanged fleet enumeration was repeated.

5. Historical aggregate GS was actually implemented and tested. The first
   report retains a 300s dominant-bucket comparison; the policy report retains
   1,200/3,600/14,400s fixed-subproblem runs, including a GS upper-only proof
   of the local interval optimum. These are neither current GI-TBC roots nor
   current full-algorithm evidence. In the equal-target tiny reference, a
   legal GS envelope with `S<=3` gives `W_GS<=3*g`; with TC and
   `Hsum<=4*W_GS`, it proves the same closure. Thus tiny closure does not
   establish superiority over all previous GS. Do not activate the diagnostic
   reverse-H row or change the comparison S domain.

6. The heterogeneous-target example in B5 is an exact pure-product separation.
   The station sums and q sums are `1` and `1/4`; all local bounds
   `0<=q<=s/2` hold. It gives `Y=(1/4,3/4)`, `Z=(0,3/8)`,
   `S=5/8, W=3/16`. The aggregate McCormick lower right sides are
   `0,1/16` and upper right sides `5/16,1/4`, all satisfied by `W=3/16`.
   Yet `J=3/8 > B*g=1/4`, a violation of `1/8`. This is not a full BRP/TC
   witness or a real-root objective result.

7. AP/IND concerns state penalty cancellation and, under the documented
   aggregate-use assumptions, projection onto `(x,P_e)`. It does not assert
   resource-product consistency. Its previous objective gains and performance
   reversals must retain their R135 identities; AP remains off for the new
   main comparison.

## Conditions for implementation review

No mathematical blocker was found. Before expensive runs, inspect the actual
root/child/cutoff-refresh/LP-to-MIP paths, switch-dependent reuse keys, and
post-preset Seed propagation. Check that the new writer preserves full binary64
variable coefficients, and conservatively rounds only new multiplied right
sides (upper rows upward, lower rows downward). The review above does not
certify a future implementation, floating-point row emission or experiment.
