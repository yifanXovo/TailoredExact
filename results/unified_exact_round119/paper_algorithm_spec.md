# Round119: incumbent-triggered contraction of an already proved interval

The complete [R118 integrated algorithm specification](../unified_exact_round118/paper_algorithm_spec.md) remains the definition of ENS-C, M-B, P and P-S. R118's results and claims are unchanged. ENS-C remains the default, cold P-GRB the primary benchmark, and frozen M-B the direct mechanism control. Round119 enables MB-PC only with the explicit `--round119-proof-contraction` flag and the original R83/gcap-frontier/M-B configuration. Its final production identity is recorded in `production_identity.json` and `candidate_identity.json`; every current formal method uses that same PE and DLL.

## Original feasible problem and inherited method

For service stations (excluding depot0), Y_i=b_i+sum_k(d_ki-p_ki), r_i=Y_i/D_i, and F=G_true+lambda*sum_i w_i*abs(r_i-1). G_true uses the original zero-denominator convention. Vehicles leave empty; a station has at most one vehicle/visit and one nonzero integer service direction. Every load prefix and loaded return is in [0,Q]. Complete route duration is travel+(pickup_seconds+drop_seconds)*total_pickup, including unloading on return. Q is simultaneous load, not a bound on cumulative pickup. `min_ratio` is not a new inventory floor. The original Parser and Evaluator remain authoritative.

The inherited H is the original joint insertion construction, 24 orders at Seed20260626 plus the constructive 25th seed, complete decoding/guided descent, R76 closure, and the R78/R83 union under the original sorted-duration rule. All H and Start work remains paid. P is cold. P-S is unchanged and is used only in finite disabled-feature qualification here; it is not an added formal performance arm.

M-B retains continuous-declared p/d, integer Y/load, binary s/z/m, and the existing A/B constraints. Unique one-way integer inventory changes retain the original integral service implication. No independent ENS-Q mode, cut family, branching policy, probe budget or neighborhood is added. The original controlling-leaf scheduler, AM, maximum depth8, minimum width, epoch-sensitive cache and same-leaf terminal guard are preserved.

## Separate archive of paid mathematical evidence

Only successfully returned, qualified finite OPTIMAL midpoint-child LP evidence that the original controller already paid for is registered in this first implementation. The archive records actual call, original scope/model SHA/path, cutoff, epoch, parent interval and depth. Existing infeasible-half contraction remains separate. An archived proof is not an old-epoch cache entry relabeled as current.

For C=(I,c,ell,embedding/return/dependencies), the statement is conditional: original feasible fleets with true G in I and F<=c satisfy F>=ell. The cutoff complement gives b_I=min(ell,c) on the entire original physical interval. With the unchanged evidence tolerance tau=1e-7, only a physically verified own U satisfying U+tau<b_I excludes I from the strict improvement domain. Neither a feasible objective nor model epigraph g establishes this predicate. Exact-g embedding represents every physical improving point in the retained model.

Candidate pairs are deterministic: ancestor depth, original parent ID, then fixed side order. Both returned halves must form the exact old interval at their actual midpoint and agree on epoch/cutoff/parent geometry. The chosen split must strictly shrink the current leaf. Each used proof is consumed once. Child depth is inherited and incremented, so a new generation ID does not reset finite-depth safeguards.

The retained interval plus all archived removed intervals and the original objective/G tails cover the complete original improvement problem. Removed sides are improvement-fathomed, not asserted physically infeasible. A global bound is the minimum of qualified bounds across the complete cover; a high removed-side bound is never used as the retained side's or parent's bound. Containing-domain bounds may pass to a subset. A subset's bound may not pass to a parent or sibling. A complete qualified cover, with a legal own U, can establish original optimality under the inherited numerical policy.

## Native event handoff

```text
Before an ordinary terminal MIP:
  check the archive against the current own physical incumbent;
  if a qualified exact pair excludes a side, atomically commit its cover.

During terminal MIPSOL:
  reconstruct and verify the original complete fleet;
  compute deterministic original F and integer Y;
  save an eligible proof event and request GRBterminate;
  leave the native model and controller unchanged inside the callback.

After the real return and cleanup:
  retain the old call/model/scope, returned status and qualified old bound;
  apply the return/error/deadline/resource gate;
  preserve the own fleet and update its epoch;
  close a sufficient old cover without rebuilding, if available;
  otherwise validate a copied scheduler transaction and commit exact children;
  archive the removed side and use a new strict-subdomain child generation;
  enter the original controller/AM, including its required LP/MIP;
  map only an eligible same-run own Start against all actual rows/columns.
```

INTERRUPTED is a real interrupted return, not OPTIMAL/INFEASIBLE. A termination request alone is insufficient. Unknown/error returns invalidate the event; resource stops prevent continuation; a reached absolute deadline permits necessary cover bookkeeping but no new Optimize. The old B&B tree, local cuts and basis are not claimed to migrate. No clock, Work, stagnation threshold, role label or historical R118 value triggers a restart. Without a new strict domain, the inherited same-leaf terminal guard remains effective.

An own incumbent may belong to another live region; an ineligible retained-region Start is cleared/skipped by the existing mapper. An unexpected mapping failure for an eligible fleet is a qualification failure. Historical routes are never substituted. Any same-scope physical counterexample revokes the numerical claim and every dependent contraction/closure/certificate. Keeping the legal own U does not repair incorrect pruning.

## Qualification, measurements and scope of claims

`mathematical_contract.md`, `preflight_replay.json`, and `qualification/` distinguish finite mathematics, actual native row/column embeddings, an actual interrupted contraction/new-domain solve, and H100 CLI checks. The weak legal initial fleet is an explicitly marked fixture-only entrance, excluded from every formal argv. `qualification/math_completion.json` also discloses the supplementary test's wrong expected empty-fleet objective, retained failed attempt, completed finite lifecycle prefix and later pure mathematical review; its corrected C++ source was not rerun.

All online evidence checks, termination delay, journal writes, model cleanup, rebuilding, Start and new native work remain inside the same T_produce deadline. Independent post-seal verification cannot feed back into a run. T_verify and T_total are separate. Exact certification-time ratios are reported only when both arms certify; signed gaps are retained. `protocol.json` fixes all nine development positions and the three conditional E50-C1 positions before the first formal start.

This is standard scoped bound pruning applied to the existing BRP representation and evidence lifecycle, not a new general bound-pruning theorem or rational B&B proof. Actual performance and the one stage decision are supplied by the completed `final_report.md` and current core records. A known development/confirmation role is not an independent geographic or statistical sample. No outcome promotes a default or authorizes another configuration grid.
