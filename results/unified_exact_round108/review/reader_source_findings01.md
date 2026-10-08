# Lightweight reader source findings

Source-only review while the serial bridge is live. No raw archive, LP/model, full reader, compiler or solver was run.

The true-G scope logic of scoped_proofs/supported_leaf_bound is appropriate: returned original LP/native bounds are local to their true-G interval and qualified cutoff. Partition the final leaf at all scope endpoints, use the strongest valid bound and F >= true G on each interval, then take the minimum across intervals. Local epigraph outsiders and local LP infeasibility cannot widen a proof to the whole domain. LP infeasibility below a qualified cutoff gives F >= cutoff in that interval, with the objective-above-cutoff complement separately covered.

Four reader evidence repairs are required before the complete reconstruction:

1. round107_reader.bound checks geometry, finite values, cutoffs and witness contradictions, but not independent prior provenance for each nonactive call.cover piece lower bound. scoped_proofs uses all calls without time restriction. complete_cover's scope_bounds corroboration cannot establish chronology itself. Validate each call snapshot at its committed sequence using original true-G floor, already returned valid LP/INF, or earlier committed typed native bounds with compatible interval/model/cutoff. Add the active call's bound at its own event. A later LP may support a final leaf but cannot support an earlier snapshot/checkpoint retrospectively.

2. LP linkage checks leaf/model/status but not the status row gamma_L/gamma_U. Bind these fields to the actual call/model interval and successful returned sequence, including cached canonical/model/cutoff identity.

3. The numeric optimal LP lower bound comes from the controller CSV; the later native log check only requires an Optimal objective line. Cross-check its numeric optimum or another actual returned native attribute with the linked LP bound at original tolerance. INF likewise requires actual native infeasibility, successful return and model/scope linkage.

4. complete_cover demands covered >= min(U,1) although journal scopes use physical gmax. For nonnegative ratios H <= (V-1)S, so true G <= (V-1)/V; zero S gives G=0. When U exceeds gmax, demanding an impossible G tail can falsely reject a complete root cover. Derive and validate the actual original physical maximum/root domain, and tie scope intervals to saved model G bounds and original cap/floor/cutoff rows.

Trace arithmetic and monotonicity do not establish chronological provenance. Complete certification still requires own physical U, independently supported full interval coverage, lifecycle completion, unresolved-flag reconciliation and the original closure tolerance. These are pure evidence qualification repairs, with no production, performance helper or frozen decision-threshold change.
