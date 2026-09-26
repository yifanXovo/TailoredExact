## Change

Round88 found useful inventory-CDF relaxation strengthening, but its repeated-LP service and eager full-family epigraph were too costly to advance. This default-off prototype separates B1 rows inside ENS-C's existing native MIP search, without a second Optimize service or a full auxiliary matrix. It adds `--round89-native-ot-b1 true` for the R83 preset and identifies the candidate separately; reference ENS-C and P-GRB defaults remain unchanged.

The separator audits the actual VD-P inventory/state and ratio/inventory links, constructs signed CDF rows on the imported model's support, and conservatively accounts for support multiplication and row-coefficient rounding. It submits every reliably violated pair row at an optimal MIPNODE, without internal time, Work, row or pass quotas. Terminal and partial-bound proof MIPs share this rule; ordinary LP probes remain unchanged. PreCrush=1 is the only new production solver setting. Callback work counts toward the original complete-run deadline, and API/model errors invalidate the candidate call instead of retrying as baseline.

Production evidence records per-MIP identities, counts, skip reasons and costs. Successful API submission is not described as permanent solver acceptance. Startup, AM gate, split policy, mathematical proof targets and certificate tolerances are unchanged.

## Validation status

The implementation and isolated test harness compile. Initial independent static review found an ineffective floating-environment guard, a missing genuinely rounded-product test, an expensive repeated matrix scan, and failure-path bound events that could be reported as valid. Targeted repairs are compiled and awaiting the reviewer's final recheck. **No new tests or Optimize calls have run yet; no performance improvement is claimed.**

The proposed qualification combines an independent exact-dyadic oracle with six isolated toy Optimize calls: off/static/callback and actual-backend LP/terminal/partial paths. Whole-method screening requires a separate evidence-based admission after qualification. This draft neither promotes a mainline algorithm nor starts a broad long-run campaign.

See [method delta](results/unified_exact_round89/method_delta.md), [plan](results/unified_exact_round89/plan.md), [source and compile handoff](results/unified_exact_round89/static_review_handoff.md), and the [reviewed mathematical contract](results/unified_exact_round88/native_ot_b1_contract_review.md). All compile attempts, including the initial macro-address failure, are preserved; the overall research goal remains active.
