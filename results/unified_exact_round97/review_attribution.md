# Independent development and attribution review

The independent reviewer read the completed F2 evidence and proposed three old-closure controls without running Optimize or editing files. The reviewer agrees these are a targeted use of the attribution reserve in revision02_plan, not confirmation or an interface/trigger/startup matrix. F2's three fresh candidate improvements equal its old-closure outputs; the overall47.515s process-cost gain cannot be assigned to R96. F5 wording must preserve its trajectory crossover and refer to the3600s endpoint. V1's interrupted status is not repaired by adding an old-operator control.

Candidate selection principles were fixed in development02_f2_report before any additional timed arm: preserve legality and F2 certification, favor the simpler old closure unless the declared material multi-role evidence supports combined, never switch per instance, retain conflict and unknown certification evidence. The projected maximum with all three controls and reserved confirmation is75141.903s and52experimental starts including existing diagnostics/micros.

The reviewer found a prelaunch queue guard omission: the runner checked an in-memory identity while campaign.run reloaded the on-disk identity. The primary agent added a bound manifest hash at admission and a per-arm check before dispatch. The initial unstarted identity and runner bytes are archived in attribution01/prelaunch_identity_v1.json and prelaunch_runner_v1.py.txt. The revised identity changes only runner/helper bindings and revision provenance; all planned launches are identical.

The actual queue mutation test in tests/round97_attribution_guard_test.py uses a separate temporary fixture: modifying the manifest after queue freeze produces stopped_failure_no_restart before the dispatcher is reached. Its engineering receipt attribution01_checks03 passed, as did actual revised-prefix admission checks04, all zero Optimize. Checks02 was a test-command quoting SyntaxError and is retained; it did not execute an optimizer or alter a run. The initial prepare/check receipts are preserved too.

The confirmation runner remains an unexecuted guarded draft and was not qualified by this review. No candidate freeze or confirmation Optimize exists.

A follow-up independent static review confirmed the specific gap is closed, new/old launches are identical, and the fixture covers the mutation-after-freeze case with dispatcher-not-called assertion. The reviewer did not execute the test or Optimize.
