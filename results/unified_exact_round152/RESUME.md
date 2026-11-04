# Round152 continuation and delivery record

The user explicitly adopted the `/goal` in [goal.md](goal.md). Its offline
object-level research stage is complete and independently accepted; publication
steps below are recorded only after their actual completion.

## Scientific handoff

- Branch: `codex/round152-resource-integer-objective`, based on verified R151
  `c6e930ffcb84f0c3801c651f28b5f7e8e2062f33`.
- Stable paper algorithm: R137 GI-TBC. Production source, entries, profiles,
  PE and DLL are unchanged. No new H or complete B/J arm was run.
- The exact small example has compatible marginals and a `53/1080` objective
  gap beyond the declared AP/GD/stock/count inventory reference. It does not
  prove dominance over every historical normalized or disjunctive hull.
- Against the stronger old RN reference, N-B35 improves from
  `0.38673718656544753` to `0.3929789535186393` through an integer scalar floor;
  K35 has no distinguishable extra LP gain; N-C20 improves from
  `0.17446526778483834` to `0.17473288430246972` through a qualified support row.
- All original variables remain free. A separated saved point is distinguished
  from a higher complete LP optimum and from full algorithm performance.
- All 274 new Native Optimize calls returned. Seven failed outer attempts
  and one undecided small pricing qualification remain in the evidence.
- Charged new experimental outer time, including independent final review:
  **851.5968562993511 seconds / 86400**. Build time is zero. Pure authoring,
  packaging and public byte-recovery I/O are separate.
- [Independent final review](review/final_scientific_review.md):
  `ACCEPT_OFFLINE_SCIENTIFIC_STAGE`, no scientific blockers.
- The next focused question is choosing potentials against multiple marginals
  on the current optimal face to make a small support-row set strengthen the
  free LP more consistently. No further experiment is required for this stage.

Read [final_report.md](final_report.md), [mathematical_analysis.md](mathematical_analysis.md),
[candidate_decision.json](candidate_decision.json), [cost_report.json](cost_report.json),
[source_manifest.json](source_manifest.json) and [reproducibility.md](reproducibility.md).

## Workspace inheritance

Future work must explicitly inherit `WORKSPACE_POLICY.md`: all new build/raw/
temp/restore assets stay under `E:\codes\ExactEBRP-work`; protect the original
`E:\codes\ExactEBRP` and its user changes. Only completed, reconstructible
current-round duplicates covered by accepted public recovery may be cleaned.
Retain unique raw, failures, necessary PE/DLL, the active tree and all old
history. Zero deletion is acceptable. This task grants no historical cleanup,
merge, force push or branch deletion authority.

## Actual publication and closeout

Fixed-science commit, public restore, English Draft PR readback and cleanup
are pending at this prepublication snapshot. Their receipts and exact
identities will be added in a delivery-only commit, without changing science.
