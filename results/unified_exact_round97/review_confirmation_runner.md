# Confirmation runner: prelaunch independent review

Status: draft runner only. No candidate freeze, reference export, confirmation
preparation or confirmation Optimize has occurred. Static findings and fixes do
not substitute for actual idle-machine admission tests.

The independent reviewer read `scripts/round97_confirmation.py` and the short
source definitions it uses while attribution01 was running. The reviewer did
not execute Python, C++, Optimize, builds, large hashes or evidence audits.

Two defects were found before any confirmation launch:

1. Checking only role/arm/window did not bind the full operator, command and
   panel, and taking a new batch hash on each run-role could admit a change
   between C1 and C2. The fix rebuilds the complete expected launch list from
   the reserved inputs, original command generators and frozen candidate; it
   compares that list exactly and retains the preparation batch hash across all
   roles. Every preceding role queue must have that same hash.
2. Three successful arms could precede a failed end-of-role cross-arm check,
   while the next role checked only the successful arm prefix. The fix requires
   every preceding role's normal completion status, matching last event, hashed
   successful consistency receipt and unchanged bound audit/completion files.

The reviewer reread these fixes and found both holes closed in the static
logic, with no new definite blocking issue. The original reserved role order,
900/1800/3600 second windows, zero-Optimize reference builder, plain original P
command, serial vector checks and stop-on-abnormal-return policy were confirmed.

`tests/round97_confirmation_guard_test.py` is drafted but NOT YET EXECUTED. It
uses synthetic reference/build identities, the actual command generators and
actual admission functions in a separate exclusive temporary fixture. It tests
changed operator/command, changed panel, stale preparation hash, a failed
preceding role and changed bound evidence. It cannot launch a research solve.
Actual qualification and receipts will be recorded after attribution is idle.

Executed follow-up after all attribution arms became terminal: checks01 failed
in the fixture because it used the research exclusive-create writer to mutate
the fixture manifest (1.3043092s, zero Optimize). The production guard had not
dispatched anything. The failed fixture and receipt were retained. The test now
uses a writer restricted to its new fixture directory; checks02 actually passed
in1.4422082s, zero Optimize, including rejection before run_one dispatch after a
preceding role failure. See engineering/confirmation_guard_checks01 and02.
