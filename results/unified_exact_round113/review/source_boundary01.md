# Round113 independent source boundary review

Decision: DESIGN_BOUNDARIES_RECORDED_NO_ADMISSION. This record is static review
of the actual inherited entry points and bounded signed R112 evidence. It does
not admit a not-yet-frozen R113 implementation. No qualification driver, fake OS
child, solver, compiler or Optimize was started by the reviewer. No production
source or performance helper was changed. Actual bindings are in
source_boundary01.json. No applicable AGENTS.md was found at the workspace or
its E:/ and E:/codes parents, or in the reviewed scripts/results directories.

## The non-authoritative publication dependency

The R112 campaign at scripts/round112_campaign.py:50 extracts the actual
scripts/round90_lp_g_g3.py run_one function into a private namespace. It changes
ROOT/CAMPAIGN and the necessary audit entry point and inserts the two paid
native-end/audit-end receipts. This makes a per-arm private atomic_status
binding possible without touching R88/R90/R112 source bytes or other arms.

Actual R90 run_one:710-730 writes the necessary samples.jsonl, publishes
runtime_status.json, advances last_sample, then checks disk and consecutive
low-memory samples. atomic_status is an alias to R88 at R90:36; R88:59-65 opens
the .tmp file, serializes with allow_nan=False, closes it and calls os.replace.
An OSError at publication currently exits the loop and reaches R90:747-750,
whose finally kills/waits the active child. This is the confirmed coupling.
It is sufficient to isolate the specific optional call. No claim about the
unique historical handle holder follows from this dependency.

The acceptable local adapter catches only OSError raised within optional
publication. JSON/value/logic failures must propagate. On the first error it
retains the current arm, clocks, path, filesystem stage, errno/winerror and
exception; it disables subsequent publication in that arm. It returns to the
unmodified original sequence, so last_sample, disk/memory checks, hard deadline,
normal poll/wait and finally still run. No sleep, retry, continue, broad IO
exception shield or deadline/reserve change is appropriate. New arm state must
be fresh. If a namespace binding is temporarily mutated, restore it in finally;
prefer a fresh private namespace per arm to avoid shared-module mutation.

The necessary degradation receipt should be written by the R113 wrapper before
its original whole timestamp. Its failure is authoritative. The old status
target, or remaining .tmp bytes, cannot become a receipt. Required launch,
journal, samples, completion, observations, audit, metrics and clock writes
retain their inherited failure behavior. Tests must cover each required failure
and cleanup without claiming that mocks executed native Windows/solver work.

## Source-supported P-S lifecycle states

The real entry point src/main.cpp:20074-20089 runs the separate original ENS H
options, saves result.json.round112.startup.json, closes/checks the file, records
H complete and then enters the original compact solver. H source, physical
fleet, Seed20260626/24+1 semantics, reserve and PE are not changed by an audit
repair.

| Path | Production evidence before normal return | Required treatment |
|---|---|---|
| startup_zero | GurobiBaseline:4397-4414 verifies own H, journals own witness, returns at the original <=1e-7 zero criterion before a model/call | Own H plus independent floor0; zero policy retained; no backend exposure or native Start adoption |
| model-before deadline | Same block returns positive own H when processWorkDeadlineReached is true; no call declared | Normal completion, actual own H and original deadline must corroborate zero Optimize; no native certificate/search credit |
| mapping-after deadline | Full original model/domain/parameter checks and Round112CompactStart submission occur; beginCall at :4820; :4829-4833 writes explicit not_started for that call with reason=no_remaining_original_work_window and actual_Optimize=false | Exactly one call and matching cancellation; preserve every already-executed matrix/Start/API/parameter check; Optimize=0/status=startup_deadline; no native incumbent/LB/OPTIMAL/cover credit |
| exposed original MIP | :4839-4844 records plain_gurobi_optimize_launch start, calls api.optimize and writes returned; count increments after return | One full original compact MIP; normal return, domain/lifecycle, complete Start and original range/bound checks retained |
| declared or launched call with no return | Not a source-supported normal cancellation solely because returned is missing | Reject a formal endpoint unless complete corroborating normal lifecycle exists; preserve partial/failed evidence, never downgrade to a zero-call success |

There is no independent started journal event in the inherited PE.
src/NativeEvidenceJournal.cpp:153-160 publishes call when beginCall declares the
scope; :206-211 publishes returned/not_started. Started counts must be checked
against real phase/log evidence, successful return and result count; no new
journal event or native execution may be invented. The absence of a returned
event is not proof of not_started.

processWorkRemainingSeconds subtracts the unchanged shutdown margin from the
entry-based remaining budget in src/ProcessPhaseLedger.cpp:50-64. A normal
startup_deadline needs corroboration from actual elapsed/deadline fields and
phase chronology, not only its result status text. Note that phase writes can
return silently on open failure in :79; a missing necessary phase record cannot
be repaired with fabricated timestamps.

## The necessary and offline dependency closure

The inherited R86 audit at scripts/round86_native_evidence.py:61-131 recognizes
identity/call/witness/bound/returned/witness_rejected but rejects not_started. It
also reports native_calls_started=len(calls). R112 audit:77-108 independently
uses the existence/count of call declarations to require Optimize=1 and exposed
lifecycle. These are the two source-supported latent audit defects; R112's
qualification.md and independent admission explicitly disclose that the
mapping-after exhaustion path was unexercised. No old data/algorithm error is
inferred.

R108 imports R107's journal reader. R107:110-143 recognizes not_started and
subtracts a set of IDs, but it does not enforce unique cancellation events,
prior declaration, reason, or no native bound/witness before cancellation. Its
returned-set and not_started-set closure is insufficient alone. R112 offline
paid_endpoint:34-59 skips Start checks when j.started=0, so it needs the same
strict lifecycle gate as the necessary audit. A new R113-local module should
own that gate; old raw/source modules remain unchanged.

The strict gate must reject duplicate declarations/returns/cancellations;
unmatched IDs, wrong sequence/reason/actual_Optimize flag; any Optimize phase,
native optimize log, native bound, native witness or returned event for a
cancelled call; unresolved actual calls and count mismatches. Require the
original ordered identity and committed receipt hash/size/times. Do not filter
events or renumber payloads to make a base reader accept them.

For an explicitly cancelled call, reuse R112 start_audit to compare the original
LP with full pre/post native matrices, every saved column and numerical row,
full finite/type/bound/integer Start values, physical objective, single real
submission and exact API readback. Compare original reference SHA/fingerprint/
dimensions and journal settings. The five requested/effective/set/get parameter
fields and version are established before beginCall. Correction after targeted
inspection of GurobiBaseline.cpp:5015: the summary flag
native_mip_strict_gap_parameters_valid is assigned after Optimize, so the full
R94 parameter_readback(require_call=True,arm=P-GRB) is suitable only for an
actually started call. A cancelled call needs the same explicit five parameter
field checks plus journal tolerance settings/domain, without the post-Optimize
summary flag. Lifecycle, solver finalization, native status and ObjBound fields
are also established after Optimize and must not be prerequisites for legal
cancellation. Nor may they contribute credit to it. Actual positive exposed MIP
rules remain unchanged. The initial JSON bindings remain a record of the source
read at the first review; this prose correction records the improved inspection.

For model-before exhaustion and startup_zero, require normal return with
necessary files, exact entry/preset/command, verified own current H and floor0,
original timing/deadline state, no declared/native activity and a consistent
result. For positive deadline return require no certificate. For zero return
apply only the existing numerical zero criterion and disclose exact integer
inventory separately. A legal mapped-but-cancelled Start remains visible as
API submission/readback evidence with BACKEND_NOT_EXPOSED native adoption.

## Bounded retained-history authority

The reviewed R112 report, incident, current summary, final-reader delta and
restored-root signature agree on BLOCKED: 12 qualified completions, one partial,
seven unstarted; 18 evaluable and 12 UNEVALUABLE positions; both vectors
WIN/WIN/LOSS/UNEVALUABLE/UNEVALUABLE. Original signed gaps, F2 certification, C2
M-B repair and simultaneous ENS/P severe LOSS plus ENS/P-S WIN, L48 P-S timing
advantage all survive unchanged. Partial arm13 cannot obtain endpoint, whole,
certificate or free Start/UB. The current R112 offline reader SHA63e388... has a
reviewed delta; its historical admission SHA d624... is not falsely required as
current bytes. No old LP matrix was reparsed in this review.

The final admission still needs the exact frozen R113 helper/source/input/argv
identity, real Windows sharing failure evidence, original-supervisor mock
coverage, legal/illegal lifecycle fixtures through actual necessary/offline
functions, targeted retained12 compatibility mapping, four H100 actual CLIs
with at least P-S's real active publication target locked, completed exact fees,
and semantic/fleet same-H evidence. Qualification evidence is not a formal
performance observation. Formal8 must remain unstarted until that signature.
Review during formal execution will pause until requested after both groups.
