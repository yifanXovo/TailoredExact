# Independent static review of final evidence processing

Reviewer: `/root/independent_review`, 2026-11-04 (Asia/Shanghai).

Decision: **ACCEPT_STATIC_FINALIZATION_PIPELINE**. This admits the finite
processing path; it does not assert that final research, the complete
panel, verification, or delivery has completed.

Inspected identities:

- `round153_finalize.py` SHA256
  `8648a42b3f8a3a77390ad594e8d8895a6848da9b4030b08adcd3ab00571c2eab`.
- `round153_audit.py` SHA256
  `444ef9e5078e826525360912187f8b9cd2e344ae32db7810011b85b2e9a97360`.
- Working `final_report.md` SHA256
  `d71a264565f6291f7fef9ee4ef277ae0ab8c2535bd5c1c5364c01c9e3eb40ec0`.

## One outer charge

Invoke finalization through one `round153_common.run` outer receipt, with
an adequate finite reservation and the required serial idle state. The
finalizer itself calls audit, science, research, complete and sources in
that order in the same process. Those functions do not open another meter,
launch a producer or compile, and the finite scientific audit performs its
declared six Native model reads with zero Optimize calls. The existing
meter rejects nested fee processes and unclosed prior receipts. This
counts processing, model reads, source checks and report construction once
at the outer boundary.

`costs()` is deliberately absent from that process. Calling it only after
the finalization child exits and its outer receipt closes includes the
last verification cost in the ledger. Its `budget()['unclosed']` assertion
rejects an early call. That later operation reads closed ledger metadata
and writes accounting tables; it is not another scientific verification
or performance rerun. The postprocessing manifest excludes `costs.csv`,
which is expected to be written later.

Finalizer admission assumes use of this outer wrapper. Directly running
the finalizer script without the wrapper would not itself create a fee
receipt. A failed finalization retains its fee and partial evidence; only
the final postprocessing PASS after all steps is the successful closeout.

## Evidence and identities

The final scientific audit precedes the scientific and research tables.
The complete-method table reads the sealed arm endpoints and existing
verification closeouts, and finalization refuses to finish with a missing
frozen matrix position. Its source check verifies all frozen candidate,
matrix-helper and loaded-helper dependency hashes, the PE and DLL, the
candidate/helper manifest hashes, and the unchanged stable entry/profile
against the fixed base. It separately records the current delivery HEAD
and current offline source hashes. Preserved per-run source byte files are
hashed against their snapshot records, so old offline versions are not
retrospectively replaced with the latest script identity.

The source manifest inventories the snapshots that actually exist. It
should not be read as proving snapshot coverage for an experiment with no
snapshot record. Any such historical bookkeeping omission must remain
explicit, as the working report already requires; it is not repaired by
rerunning the experiment. Frozen production runtime identity remains
subject to its stronger previously reviewed handshake and arm evidence.

The postprocessing record hashes the scientific audit, source manifest and
generated reports after these checks. It is a processing closeout, not a
replacement for the outer receipt or the final delivery/recovery record.

## Working report scope

The inspected report opens with an active-goal statement and explicitly
leaves K35/NC20 deepening, all eight complete outcomes, final verification
and delivery pending. Its upper-bound distinctions, single convexity
correction, CDF probe limitations, inherited numerical-primal policy and
cost separation are consistent with the admitted design. It does not
convert a wide checkpoint into a scientific negative result or a completed
performance sample. Its live paragraphs and fee totals must be replaced
only by the final qualified evidence.

The reviewer only read small source files and drafts and wrote this review.
No Native, replay, enumeration, compilation or heavy-I/O verification was
run. No new review of the unchanged frozen production implementation was
needed for this processing change.

## Timing disclosure wording correction

**ACCEPT_STATIC_MANIFEST_WORDING_CORRECTION** at inspected
`round153_finalize.py` SHA256
`e91eb37e7d4d65b0cc9b1285c62cdea4f57f2d92d1d31e9ba1c118115a2ab2fe`.

The source manifest now records
`source_snapshot_and_identity_bookkeeping_before_outer_receipts_not_separately_timed=True`
and `untimed_setup_is_disclosed_measurement_gap_not_zero_cost=True`.
The previous `unmetered_pure_IO` flag is absent. This correctly distinguishes
an untimed setup/identity-check measurement gap from a claim that such
work costs zero or has been classified as exempt pure writing/public I/O.
It aligns the manifest with the cost and reproduction disclosures.

This limited review concerns those explanatory output fields. They do not
change source identity checks, the admitted serial processing sequence,
the six Native model reads, or the zero-Optimize audit contract. No program
or verification was run, and no producer rerun or retrospective cost
estimate is required for this correction.
