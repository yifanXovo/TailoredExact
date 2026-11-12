# Round163 independent agent review: mathematics and method

Reviewer: `/root/round163_math_review`, a separate Codex agent invoked under
goal section H. This is an independent agent readback, not human peer review.
Review date: 2026-11-12. Worktree: `E:/codes/ExactEBRP-work/worktrees/round163`.

Status: **PASS for the bounded mathematics/method review, including final
manuscript and algorithm-choice readback.** No unresolved conclusion-changing
mathematical or method defect was found. This status is subject to the
explicit static-review limitations below.

## Scope and identities actually read

I read `goal.md`, root `WORKSPACE_POLICY.md`, `method_freeze.json`, the actual
`matrix_frozen.json` commands for P/B/E+, its complete 18-position method/cap/
Seed ordering, `helper_manifest_Eplus.json`, `science_identity.json`, and
`scripts/round163_campaign.py`. I inspected the maintained R137
`paper_body.md` (physical/algorithm sections, structural integration and
current conclusion/priorities), `mathematical_analysis.md` (including the new
structural synthesis), the existing numerical-policy/model sections and new
protocol insertion in `supplement.md`, and Appendix A and the qualification/
coverage portions of `model_and_algorithm_appendices.md`. The new
`structural_synthesis.md` and `historical_source_map.json` were read directly.

The measured C++ identity reported in `science_identity.json` is
`e920b92e199e825ec89a2932f701861ff158e0d4`, PE SHA256
`fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93`,
and Gurobi 13.0.2 DLL SHA256
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`.
My static `git diff --name-only` against that measured commit lists only the
separately disclosed non-Gurobi `Round160PhysicalNeighborhoodStub.cpp` in
`src/include`; this is consistent with the recorded production identity.
This review did not independently rehash or relaunch the PE/DLL.

I read the actual implementation portions in
`CplexBaseline.cpp` (canonical variable types, routes, one-way/nonzero service,
prefix recurrences, return/handling, inventory equations and shared states),
`Round98StateService.hpp`, `Result.cpp`, `Evaluator.cpp`,
`PhysicalWitnessValidation.cpp`, `IndependentObjectiveProof.hpp`,
`NativeEvidenceJournal.cpp`, `ControllingLeafScheduler.cpp`,
`ExternalGiniTree.cpp`, `PaperExternalGiniTree.cpp`, `GurobiBaseline.cpp`,
`Round153Research.hpp`, `Round154Research.hpp`, and default-off declarations/
CLI parsing for the noncandidate mechanisms. The helper entry actually read
is `scripts/round156_online.py`, SHA256 recorded as
`288647297aadec59d6116b8363bd91a4ce6110b51f0e2c798d5a721c9ec6bbd4`;
its parser, exact-stock and pricing routines were read in
`round151_math.py`, `round152_math.py`, and `round153_pricing.py`.
The current helper manifest identity is
`1cbb9c603f1c14e926a95fa3a1f188a3cf1c70b5f3a762655fc24404658f0ebe`.

For historical claims I used actual pinned Git contents, not just the new
source-map assertions: at `faa22ce4804f925081fd05322262b4f7261db51f`, the
R133 `joint_objective_gap_note.md`, R143 `mathematical_analysis.md`, R152,
R155 and R156 reports, and R161 formulation were read in substantial relevant
sections. Relevant report extracts from R138/R140/R145/R147/R150/R151 and
R157/R158/R159/R160/R161 were also read for the claimed positive and adverse
outcomes and their restrictions. At fixed R162 science
`fb087d7d9a3eef5bbff250487639d89b6e794739`, I read the relevant final-report
sections and the complete six-arm CSV. I did not replay those historical
producers, carriers or hidden search trees.

For the current panel I read `reports/complete_arms.json`,
`reports/comparisons.json`, `reports/summary.json`, all six actual E+ root
receipts, helper source/response/pricing summaries and
`external/round154_proof_ledger.json` files at their matrix destinations.
I inspected the X35 actual Native call/return/quality journal entries and
full proof-placement audit, B20's positive certificate endpoint and cold-P
parameter receipt, and the physical evidence format/representative complete
fleets. Existing per-arm qualification/verification receipts are evidence
read here, not newly executed checks by this reviewer.

## Decisive findings

1. **The original physical/integer correspondence is stated with the right
   premises.** Unique assignment plus binary direction and integer initial/
   final stock fixes the sole nonzero service quantity to an integer. M-B's
   shared movement/visit links are valid strengthening, not an extra premise
   for that implication. The actual writer retains binary directions and
   nonzero-service rows, integer final inventory and prefix loads; M-B alone
   relaxes the redundant service quantity declarations. Empty departure,
   prefix capacity, loaded return and final unloading match the validator.
   In particular, return conservation gives
   `max(0,B-sum Q)<=sum Y<=B`, while handling is `(tp+td)*sum pickups`;
   cumulative pickups are not limited by fleet capacity. The native G
   variable is an epigraph, and the paper correctly distinguishes physical
   objective-preserving extensions from arbitrary inflated-G completions.

2. **The interval helper's objective/domain are faithful to the code.**
   `stock_value`, `evaluate` and the normalized pricing model use
   `max(gamma_L,G_true(Y))+sum h_i(Y_i)` with `G_true<=gamma_U`.
   They do not add a true-G lower restriction. Actual helper `omega` is the
   loaded canonical objective coefficient, already containing lambda;
   no second lambda is applied. `S=0` is evaluated as true Gini zero and is
   handled separately from the reciprocal model. Exact hard-total DP is a
   legitimate relaxation/fallback, and an unexpected Native status does not
   prove the positive branch empty. NodeLimit16384, original absolute
   price gap `1e-4`, `old_joint=True`, fresh root-once operation and the
   whole-method remaining deadline are present in the actual entry.

3. **Proof-only scope and coverage are substantive, not inferred from a
   label.** The C++ embedder binds input, objective coefficients, total
   bounds, supports, first canonical source, gamma interval and own cutoff;
   descendants must narrow that scope. `complete_root` additionally demands
   the single complete L0 root. `Round154Research.hpp` copies the scheduler
   solely for proof collection, merges `min(root_cutoff,lower)` only into
   covered final leaves, and takes the covering minimum after same-domain
   maxima. The formal-row path is bypassed by `proof_only`. All six actual
   ledgers say complete root, qualified/live source, zero Native floor rows,
   raw-AM preservation and `proof_stopped=false`. No current certificate is
   represented as a new floor-induced certificate.

4. **The preserved R133/R134 distinction is correct.** Raw restricted
   source claims are checked before cutoff clamping; the complement supplies
   its cutoff floor. Same-domain lower bounds combine by max, covering-union
   bounds by min, and exact interval comparisons prevent fabricated coverage
   gaps. A revoked source discards dependent closures and restores an open
   full domain with an independent nonnegative bound. The separate exact-zero
   predicate uses integer ratio/target conditions and repeats complete fleet
   verification. Ordinary positive Native/outer certificates still use the
   declared floating-point qualification and closure scale. The manuscript
   does not call them exact rational MIP proofs. Depth/width limits bound
   refinement but do not prove every terminal source or force certification
   within a time cap.

5. **The actual zero/near-zero observations support the stated boundary.**
   X35 has `Bminus=0`; its actual pricing result includes `zero_lower=1.0`,
   safely combined with the positive branch by min. C35 instead returns the
   near-zero inventory interval
   `[3.99954800422003e-17,6.512277257912478e-17]`, reflecting the loaded
   binary64-coefficient inventory calculation; this is not an exact physical
   zero proof. Its physical U remains `.12956638965196035`, final qualified
   search/proof L `.019837502821060043`, and state OPEN. None of the six final
   physical objectives is zero. A numerical near-zero helper value therefore
   never supplies a new physical certificate or a redraw reason.

6. **The only final E+ proof improvement is supported by its own ledger.**
   On X35, own root SHA
   `6c613d7cb2990d07b840c6e7fe849bbac3494cc3dd2958b1fa1271309ebb17a2`
   binds cutoff `.60086928090394731`, gamma interval `[0,cutoff]`,
   `Bminus=0,B=75`. The final leaf cutoff `.45747531701601757` is narrower.
   The helper floor `.42319954961578576` exceeds its raw search lower
   `.39492875817006656`; the proof lower is the former. Relative to B's
   `.3949882559151472`, the final proof gain is `.028211293700638573`,
   while raw search L is lower by about `5.95e-5`. Physical U is identical
   at `.45747531701601785`; both remain OPEN. On C20/B20/X20 the final
   search lower even exceeds the returned inventory upper. On B35 the
   capacity-limited floor `.11803645384434823` is dominated by final search
   L `.12023400258397535`; its inventory upper `.1324235571810887` remains
   above that L. C35 is the near-zero case above. These are different
   explanations for absent final gain, not evidence of universal saturation.

7. **The structural synthesis preserves the important inference limits.**
   The R133 exact `1/4` gap is on a fixed positive-total slice and its
   loaded-coefficient physical optimum also accounts for all legal return
   totals; it is not a variable-denominator Jensen theorem. R143 RN addition
   and R161 RN replacement have different continuous-domain relations.
   R157--159 finite family exclusions/UNKNOWN outcomes do not become global
   original-objective lower bounds. R162's matched free LP increment and
   5348-term projection are retained together with the six complete adverse
   PC outcomes. Its duration ablation proves conditional necessity given
   the remaining Q, not time-alone sufficiency. The standard gap identity
   separates incumbent error, physical/inventory relaxation gap and inventory
   bound precision; only the last is controlled by the same-scope inventory
   width. The new B35/X35 capacity-limited widths must not inherit R156's
   exposed-scope near-tightness claim.

## Conclusion boundary and remaining readback

The panel evidence supports a limited stage choice: B/E+ each have 3/6
certificates and identical physical U on all six; E+ supplies one final
OPEN proof-L gain, pays its helper on all six and is nominally slower on
the three jointly certified cases. B/E+ versus P is an integrated-method
comparison, not isolated GI-splitting attribution. The C35 opposed U/L
result against P must remain visible. No combined best-of-B/E+ method,
unseen-city claim, independent demand sample, universal ranking or stable
runtime distribution follows. The final recommendation may weigh the real
X35 proof gain against the complete paid costs, but must retain these facts.

I made no source/config/data/raw changes, ran no solver/H/helper/model build,
and executed no scientific checker or new reconstruction. PowerShell/rg/Git
reads were used to inspect existing text and JSON, including simple field
presentation. This is a bounded static mathematical/method review; the
parent's separately metered final source/route/identity checks are not
misrepresented as a fresh executable verification by this reviewer. No public
semantic/performance rerun, human peer review or exhaustive review of every
historical carrier member is claimed.

## Final manuscript and decision readback

After the parent reported completed integration, I reread `decision.json`,
`final_report.md`, the maintained body abstract, new section 6.5/Table 13,
replaced conclusion and sole next-question section 7.1, the mathematical
analysis's interval/coverage/gap account, the completed R163 supplement
insertion, and `docs/round163_stage_confirmation.md`/`docs/current_mainline.md`.
I also read the relevant source text in `scripts/round163_decision.py` after
the final prior-art correction. These current Markdown sources are correctly
distinguished from the older R137 PDF snapshot.

The final B-main/limited-uniform-E+ recommendation is supported as a declared
tradeoff, not a uniquely forced mathematical ranking. It explicitly weighs
the serious uniform-E+ alternative: one material X35 proof gain, no U/CERT
loss, about `.74%` more aggregate audit-inclusive cost, but higher observed
paid times on all three jointly certified configurations. Small timing
differences are not promoted to stable runtime effects. All 18 endpoints,
the C35 U/L opposition against P, single-Seed/same-archive limits, X35 raw-L
regression and the new B35/X35 capacity-limited inventory widths remain
visible. No per-instance mixture, released-default change or universal
dominance claim was introduced.

The next-question prior-art boundary required attention. I directly read
`scripts/round96_fixed_route.py`, its qualification source, and the pinned
R96 `fixed_route_report.md`. The old diagnostic already defines the proposed
owner/order skeleton domain, allowing all serviced-station integer stocks,
both signs, optional DAG zero deletion, fixed unserved stocks, prefix loads
and complete handling/return. Thus that domain and one-hot-Gini formulation
cannot be claimed as a new mathematical object or mechanism. The final
`decision.next_question_prior_art` pins the inherited script to
`faa22ce4804f925081fd05322262b4f7261db51f`, recorded Git-bytes SHA256
`40e427fa5dcffe6a11f9590109b8bc005a754b76283409d5daf02da588776821`.
The corrected decision, body and report now explicitly require reuse/
reconciliation with the current objective, zero, numerical and support
contracts, parent containment, completeness and affordable additional
information; otherwise the proposed work stops at its prerequisite. Only
configuration-specific C35 target-attainability could be new. No R96 or
other next-stage query was run here. A restricted lower is not a global
physical lower, and UNKNOWN is not infeasibility. The stated C35 incumbent
deficit lower bound follows from its independently feasible P witness,
without allocating the whole proof gap to physical coupling.

That correction is resolved on final readback. This review has no remaining
scientific blocker and requests no new scientific execution. Publication,
public recovery, final identity sealing and cleanup are the parent's
separate remaining delivery responsibilities, outside this review's
mathematics/method acceptance.
