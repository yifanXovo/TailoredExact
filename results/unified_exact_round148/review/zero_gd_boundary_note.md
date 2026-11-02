# Confirmed zero-GD reader filename boundary

Independent reviewer: `/root/round148_independent_review`. This note uses only
light source inspection during the serial K35 pair. No frozen helper,
production file, model, Native call or result was modified; no Optimize,
commercial Native load, compile or model-tree scan was started.

The boundary is real in `scripts/round147_read.py:36`. When
`round146_root.json` reports `rows == 0`, `root_context` enumerates
`*_generation_*.lp` and calls `.group(1)` on the narrower anchored expression
`_generation_(\d+)\.lp$`. The glob includes both
`L0_epoch_0_generation_1.lp` and the valid appended
`L0_epoch_0_generation_1_round148_shared_S.lp`. The latter has no match for the
anchored expression; the sort key raises `AttributeError` before the actual
root model, positive denominator or row validity can be examined.

This is a reader qualification failure, not a production-oracle failure. A
positive-S root can have zero old high/low GD rows and a nonzero shared-S row;
the independent two-site strict fixture already establishes that domain. The
production GD expected map registers the original SHA even for zero GD rows,
and Round148 copies that expected vector under the appended SHA. A filename
suffix cannot be used as a proxy for applicability. The current K35 path has
nonzero old GD rows and does not enter this fallback, so this finding does not
invalidate its admitted, currently running pair.

After both K35 timed arms finish, prefer the parent's proposed **current-run
source SHA selection** to filename ordering. In a Round148-local
`root_context`, when GD is enabled, the metadata exists with `rows == 0`, and
this run has `round148_selection.json`, use its `source_model_SHA` to find the
unique actual immutable pre-append D root. Its current `source_call` must bind
to that same model SHA in the accepted call/ledger evidence; retain that check
in the ordinary verifier. Parse this source model and recompute `actual_spec`
and the old arithmetic block. Require zero old GD rows, the declared
applicability and unchanged Bminus/B, exactly as in the inherited context
checks. Do not invoke the inherited filename-sort fallback after locating the
SHA-bound source. Other branches continue through the original R147 function.

This is more precise than a suffix filter because it identifies the actual
root that produced the slope input, even if another original-generation file
exists. It also handles `selection.ready == false`: a real source SHA can
still identify the root when no useful row was selected. Do not require a
nonempty old GD block, silently omit the context, or interpret a selection
file's mere existence as evidence of a valid current call. Fail on a missing
or nonunique source match. An exact-original filename filter remains a simple
way to harden a general fallback, but is unnecessary for this targeted current
Round148 branch.

Prefer a Round148-local `root_context` view injected into the cloned inherited
verifier, so the sealed R147 reader and old D/stable entries retain their
bytes. A short local special branch for SHA selection and the existing
arithmetic/context checks is easier to review than a directory facade or a
global monkeypatch. Keep the executed K35 wrapper identity (`33f6...`, as
recorded by the parent) and producer seals; record the post-run reader-only
hash change and any necessary read-only revalidation fee. No production
rebuild, new Optimize, formal-arm restart or new performance panel is needed.

The focused zero-Optimize fixture should contain an actual saved zero-GD
original model, a distracting Round148-suffixed filename, and a second original
whose generation number would sort earlier than the source. Bind the fixture
selection receipt to the actual source SHA. Check that the source is selected
by SHA regardless of filename ordering, and that the actual model/support and
zero-GD domain are recovered. A harmless comment can distinguish an appended
filename's bytes for this filename-transport test; do not present an invalid
affine extension of a zero-S domain as a mathematical qualification. Test a
missing source SHA and a duplicate byte-identical source match as explicit
failures. Test a current-call/model mismatch in the verifier binding.

Reuse the existing positive-S/zero-old-GD two-site driver result to establish
affine eligibility independently; it already produced the strict nonzero row
with no solver. If a complete saved positive-S/zero-GD original is available,
run the combined context sample on it as well. No new Optimize or full solve is
needed solely to combine these checks. Retain the existing zero-lower-S
omission and H-no-model samples. The old nonzero-GD branch should return the
same context as before.

Admission scope: fix and qualify this reader boundary after the active pair,
then apply the post-run reader to any affected future positive-S/zero-GD arm.
Do not expand the shared-S algorithm or buy new full runs to demonstrate a
filename fix.

## Static review of the proposed, uninstalled helper

The proposed `round148_context.py` correctly selects the unique source SHA,
recomputes the actual old-GD domain, and delegates unaffected branches. The
boundary script labels its support schema and synthetic call stubs accurately;
it does not claim they are new routing/Native evidence. The interference and
missing/duplicate-SHA cases are appropriate and require no Optimize.

One installation blocker was found in the initial `source_call_check`:
`not call['native_preconditions']` is asserted directly on raw observation
payloads. In the sealed qualification source call, the raw field is `1`.
`round133_read.py:409` changes it to `False` only in its normalized journal,
using the actual controller solve kind. Thus a synthetic `False` stub does not
exercise the actual raw contract. Bind raw call SHA/leaf/native-log identity to
the corresponding actual controller LP row, or explicitly accept the already
normalized journal instead. Preserve the original raw field. After correcting
that interface, add a labeled raw-flag-true LP unit case and validate once on the
already sealed qualification source call; reject a matched MIP row. This is a
reader-only correction and does not justify changing or rerunning the active
K35 producers.

The post-K35 revision resolves this blocker: `source_call_check` now accepts the
actual optimization ledger and requires a unique matching SHA/leaf/native-log
row whose `solve_kind` is `LP` and return code is zero. It preserves the raw
precondition flag. `qualification_reader_real_source_binding.json` reports
the actual sealed source's raw flag `1` and accepted LP kind, with producer and
verification component hashes unchanged. The zero-GD schema and saved-model
boundary receipts pass. A full closed-verifier reentry attempt was rejected;
the subsequent targeted binding check did not delete or bypass the closeout.
The parent discloses that the old wrapper regenerated the legacy arithmetic
derivative before reaching its guard, preserving its mathematical content but
changing its timing bytes. The new early guard prevents that side effect on
future closed reentry. This is a reader-only revision, with no production,
Native, endpoint or PE change. The original K35 executed-helper identities
remain sealed; RB35 freezes the new helper identities separately.
