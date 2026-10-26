# Round109 evidence reconstruction

The frozen engine is the unchanged R108 PE, SHA
`4647ee9f146a010ae4bc48f191ec12d4b9113e167b8eeccf0e43a3764e0a8ee0`,
with actual Gurobi 13.0.2 DLL SHA
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`.
Production source content is inherited R107 delivery
`b5db3f038f64215766a54498d8acc82e384de733`; Round109 starts on R108 delivery
`d11c94d81e6a2c5dcd64dad8c54b390f3cb4a027`. All 205 source bindings,
12 inputs, protocol, complete 42 argv and qualification are pinned separately.
Scientific stage is BLOCKED by the actual arm25 V100 entry stack overflow;
24 normal endpoints remain valid, one arm failed and17 never started.
Current delivery status is in `RESUME.md`; public operations remain pending
until their actual execution receipts are added. `main09_stack_failure.md`
records the independently diagnosed resource boundary.

## Exact public carrier and explicit root

`round109_public.py` adapts the validated R108 deterministic compression,
strict plain-file manifest, exact splitting and restoration implementation.
Only this round's paths, payload inventory and small pinned historical
dependencies differ. It includes current raw models, Start vectors, native
logs/journals/commits, controller/cover ledgers, own routes, complete timing,
fees, qualification, failures, actual source bytes and readers. It excludes
PEs, DLLs, compiled libraries, licenses and credentials. It does not package
the old R105–R108 raw archives.

A compressed stream smaller than 95 MiB remains one blob. An actually larger
stream uses contiguous 90 MiB exact-byte parts, without recompression. The
manifest binds each file and part, contiguous offsets and the combined
compressed SHA/size. Export/restore reject missing, extra, reordered,
overlapping or hash-mismatched parts before extracting raw evidence.

Use the tested CPython 3.12.7/GCC UCRT 14.2.0 64-bit Windows runtime when checking
exact float field values. Reconstruction is standard-library only and never
loads a solver. All destinations must be fresh directories. Example commands
(replace the bracketed directory names with new absolute paths):

```powershell
python scripts/round109_public.py export --root <published-checkout> --out <new-public-only-root>
python <new-public-only-root>/scripts/round109_public.py restore --public-root <new-public-only-root> --out <new-recovered-root>
python <new-recovered-root>/scripts/round109_finalize_blocked.py rebuild --root <new-recovered-root> --out <new-recovered-root>/rebuilt --compare <new-recovered-root>/results/unified_exact_round109/reports_final
python <new-recovered-root>/results/unified_exact_round109/review/round109_independent_blocked.py --root <new-recovered-root> --public --out <new-recovered-root>/results/unified_exact_round109/review/<new-exclusive-review> --reports <new-recovered-root>/results/unified_exact_round109/reports_final
```

Retained absolute native paths map only into the explicit recovered root.
There is no original-worktree fallback. Public independent mode requires the
PE to be absent and accepts no DLL argument. Its actual restore receipt must
identify that recovered root and attest public-file-only reads; it is written
only after a successful actual restore.

The main reader reconstructs every published CSV field and decision/summary
JSON from raw physical, model/type/Start, native and full-cover evidence. It
keeps the 12 Seed 0 main inputs and three repeated Seed 1 roles separate, retains
signed gaps and applies the original certificate/materiality/severity rules.
The independent reader uses separate core physics/cover/decision arithmetic.
Exact all-field comparison and independent recovered-root receipts will be
published as supplements outside the immutable carrier, avoiding circular
hash claims. This is mathematical/evidence restoration, not an independent
engine performance experiment or reproduction of wall-clock times.

## Measured entry and retained repairs

Formal performance uses one directly invoked Python wrapper per frozen group,
with three original PE children for each main role and two for each Seed role:

```powershell
D:/msys64/ucrt64/bin/python.exe scripts/round109_campaign.py billed campaign FIRST LAST LABEL
```

Ranges 1–3,4–6,…,34–36 are the main panel;37–38,39–40,41–42 are the Seed panel.
Exclusive destinations and next-only checks prohibit implicit reruns. Each
group reserves all remaining fixed caps/starts/overhead before launch. Full
formal time runs from actual arm admission through startup, native work,
required writes and physical/scope audit/crosscheck; legacy supervisor time
remains separate. Fee timers include process startup and closure, and native
times are never added twice. Physical horizon, cap and complete time differ.

The initial qualification wrapper failed before any child because a snapshot
loop reused the campaign-name variable. The exact source and no-child failure
remain charged. Its retry completed four children, then the Seed 1 P audit
exposed the inherited journal's hardcoded Seed 0 prerequisite predicate.
Actual requested/effective Seed 1 and other native settings were correct.
`evidence_compatibility.md` describes strict reader-only scope reconstruction,
actual source/model/type/return gates and unchanged raw false/global-null
flags. The failed fourth full qualification clock was never recorded: it is
null, with the original supervisor seconds separately published.

The final qualification child consumed its exact previously paid, unstarted
slot once; only its new wrapper start was additionally charged. Original
failure declarations were never refunded. Qualification completed 15 starts
and 477.86253422428854 outer seconds, with five actual CLI children and 17
returned Optimize calls. The original 8-start plan and both compatibility
replans remain. Formal 57 starts give the fixed 72-start limit with no reserve.
The independent admission accepted current PE/DLL, all 42 argv, twelve original
reference matrices, actual LP/MIP/Start paths, Seed readbacks and legal full
terminations before the first formal arm.

The earlier idle-guard reader-adaptation refusal launched no child; its exact
whole-script timer/snapshot was not captured. The subsequent actual adaptation
and qualification raw rebuild passed with source/command/exit receipts.
`round109_make_reader.py` is authoring history; do not rerun it over later
reader repairs. A read-only live-PID inspection also raced a normal P exit;
its tool diagnostic and honest missing-stream/timing limits are retained.
Successful subsequent live module inspection matched the actual loaded PE
and DLL paths/hashes. Editing/manual engineering intervals not measured are
unknown. No repair changes the frozen algorithm, input draws or thresholds.

main05's original offline cross-arm guard stopped after three normal native
returns: P's positive native lower bound contradicted ENS's physical F=0.
The exact raw/model diagnosis and its full exact-binary64 feasible vector are
under `review/cross_arm_diagnosis02/`. The immutable known-call numerical
sidecar is `campaign/reader_recovery/main05_numerical01.json`; it rejects that
call's native bounds and independently proves P's own full-domain floor L=0.
P stays uncertified with its own U. `numerical_finite01/audit.json` contains
the actual 40 finite rejection checks. The affected partial raw rebuild is
`reports_numerical_recovery01/`, with its actual engineering source/launch/
stdout/stderr/exit receipt. Original failed wrapper/raw files are retained.
P's exact full clock remains null, with conservative recorded interval
[1770.375,1771.833281] seconds; later repair time is separate. The three
pair classes are unchanged. Independent implemented-recovery admission,
rather than the earlier conditional contract, is required before resuming
the never-started group6. Unknown later contradictions still stop at the
original guard. Detailed mathematical/timing gates and failure disclosure
are in `evidence_compatibility.md`.

## Implemented second numerical evidence recovery

Original main06 ran arms16/17 and stopped before the already declared arm18.
P17 returned normally with its own full physical F=0 fleet, but an earlier
positive callback bound contradicted that fleet. The journal failure latch
retained failure142 and suppressed its returned event. No journal return or
whole-arm clock has been manufactured. Independent raw return-code, native
log, normal process completion, serialization and complete cleanup evidence
prove the actual functional return; the published journal and actual-return
counts remain separate.

The exact-tuple recovery in `round109_main06_recovery.py` rejects every P17
native lower claim and combines P17's own complete zero fleet with its own
nonnegative full-domain objective floor. The exact complete clock remains
null, with conservative interval [643.7820000000065,645.352919] seconds.
The separate `round109_interval_pairs.py` evaluates the unchanged time and
severity rules over both complete-clock intervals. A classification counts
only when every possible endpoint combination has the same result; exact
time gains and ratios stay null. This changes evidence qualification, with
no change to the production algorithm, thresholds or measured data.

Original failures, both repair revisions, the exact reference-vector
diagnosis, finite counterexamples, actual affected-reader reconstruction and
before/after scientific comparison remain public. Details and hashes are in
`main06_recovery.md`. Independent implemented admission02 is ACCEPT and binds
the five current recovery sources, immutable sidecar02, prepaid plan02,
42 original argv, candidate identity, all fees and remaining resources.

After that actual admission, only these direct supplemental commands run:

```powershell
D:/msys64/ucrt64/bin/python.exe scripts/round109_prepaid_wrapper.py billed main07_prepaid01 18 21
D:/msys64/ucrt64/bin/python.exe scripts/round109_prepaid_wrapper.py billed main08 22 24
D:/msys64/ucrt64/bin/python.exe scripts/round109_prepaid_wrapper.py billed main09 25 27
D:/msys64/ucrt64/bin/python.exe scripts/round109_prepaid_wrapper.py billed main10 28 30
D:/msys64/ucrt64/bin/python.exe scripts/round109_prepaid_wrapper.py billed main11 31 33
D:/msys64/ucrt64/bin/python.exe scripts/round109_prepaid_wrapper.py billed main12 34 36
D:/msys64/ucrt64/bin/python.exe scripts/round109_prepaid_wrapper.py billed seed01 37 38
D:/msys64/ucrt64/bin/python.exe scripts/round109_prepaid_wrapper.py billed seed02 39 40
D:/msys64/ucrt64/bin/python.exe scripts/round109_prepaid_wrapper.py billed seed03 41 42
```

Each command reuses the frozen native supervisor, affinity, actual native
argv, cap and required audit. Arm18 consumes its exact original paid main06
slot once; main07_prepaid01 bills one wrapper and three newly declared
children19–21. This is four new conservative starts for four actual children,
not a refunded failure slot. All later wrappers bill their original normal
counts. There is no extra OS driver process. Never relaunch these commands
over existing results; they document the actual continuation, and exclusive
paths and source-bound next-only guards enforce that restriction.

Any unknown later contradiction still stops the original audit contract.
Neither known-call recovery is a generic floor fallback. No heavy reader,
independent review, compilation, packing or restoration runs concurrently
with the native performance campaign.

## BLOCKED raw reconstruction after actual arm25 failure

No native resumption is authorized after the independent actual
`main09_stack_diagnosis03` result. The finalization freeze binds that review,
all closed original fees,42 argv, input eligibility and the unchanged five
admitted recovery sources. The source-bound finalizer invokes the complete
existing raw reader, then the existing stage function with the actual fault.
It preserves `inherited_raw_summary.json`, publishes BLOCKED, and inventories
24 normal arms, failed25 and unstarted26–42. All six formal Seed1 arms are
unmeasured. Missing-data gate placeholders do not establish Seed sensitivity.

The exact published report regeneration command is:

```powershell
D:/msys64/ucrt64/bin/python.exe scripts/round109_finalize_blocked.py rebuild --root EXPLICIT_RESTORED_ROOT --out EXPLICIT_NEW_REPORT_DIRECTORY --compare EXPLICIT_RESTORED_ROOT/results/unified_exact_round109/reports_final
```

The destination must be new. Every published CSV field and every report JSON
is compared exactly, including the BLOCKED decision and inherited raw
summary. Use the frozen `blocked_finalization_freeze.json`; do not regenerate
the freeze during restoration. The restored root contains all required raw,
reader sources and diagnosis. Its paths are explicit and no original-worktree
fallback is used. Actual public export/restore and comparison receipts are
delivered separately; the operation is evidence/mathematics reconstruction,
with zero Optimize and no performance rerun.

The independent restored-root entry is
`results/unified_exact_round109/review/round109_independent_blocked.py`.
It independently computes the incomplete-panel stage from own raw physics,
full vehicles, actual models/Starts/calls/cover and fees, then checks reported
facts. Public mode takes no DLL and uses only the fresh restored root. Local
PE inspection is retained evidence, rather than a claimed new public engine
inspection. Actual final independent commands and receipts accompany the
delivery.
