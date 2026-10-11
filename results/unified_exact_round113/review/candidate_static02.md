# Round113 candidate static review, before qualification

Decision: HOLD_PENDING_TARGETED_CORRECTIONS; no admission is signed. This is a
pure source review of the initial R113 common/progress/audit/campaign/initialize
candidate. No tests, qualification driver, child, native API or compiler were
started. The findings were sent to the implementation agent before actual CLI
qualification. Production and performance helper changes were not made by the
reviewer.

Two source-confirmed defects would reject every actually exposed P-S CLI and
should be fixed before spending qualification slots:

1. ps_journal/event_lifecycle does not return return_sequences, although
   R108 cold_returned_bound indexes j['return_sequences'][call_id] for its
   linked returned proof. Populate the original returned payload sequence,
   without changing/renumbering events.
2. ps_journal requires journal identity.preset to equal the effective P-S result
   preset. NativeEvidenceJournal.cpp writes options.algorithm_preset directly;
   the original P-S argv leaves it custom. The real retained H100 P-S
   event_1.json is preset=custom/method=gurobi, while its result has the effective
   research-round112-self-paid-ens-start-original-compact identity. Validate
   those separate source-supported identities. Do not alter production/events.

The implementation agent also identified a correction to the first static
review: native_mip_strict_gap_parameters_valid is assigned after Optimize at
GurobiBaseline.cpp:5015. Explicitly check five requested/effective/set/get
parameter fields, version, journal tolerance settings and domain for a mapped
cancelled call; reserve the inherited strict summary flag/lifecycle check for a
started MIP. source_boundary01.md now records this correction.

Restore actual launch.json command equality with the frozen command in the
shared P-S gate; the previous offline paid endpoint checked this. The initial
phase gate checks counts but needs source-order validation: H start before H
complete; H complete before mapped start/complete if present; mapping before
Optimize phase if present; all handoff/Optimize phases before the unique final
serialization start, then complete, then process_exit. The normal deadline
path requires corroborating original work exhaustion. A missing returned event
still rejects; no state may be downgraded to not_started based on absence alone.

The optional publisher design otherwise retains the intended narrow scope:
fresh per-arm publisher in a private supervisor namespace, only OSError caught,
single retained error with errno/winerror/path/clock/stage, no retry/sleep, normal
return to original last_sample/resource/deadline checks, no old source mutation.
The necessary publication receipt is written in supervised finally before the
outer whole timestamp; its failure propagates. The qualification holder targets
the actual campaign runtime_status.json and stays in the wrapper process,
without adding an undeclared OS holder. These are source observations, not yet
claims of executed Windows or solver coverage.

Other reviewed preparation boundaries preserve the inherited PE/DLL/206 source
binding and copied original references, fixed eight formal/four H100 argv,
21600 formal nominal seconds, two groups with 120 each outer reserve, 28/26000
total and 12/1200 qualification limits. Exact final candidate helper/test/raw
identities and closed actual fees remain pending independent admission.
