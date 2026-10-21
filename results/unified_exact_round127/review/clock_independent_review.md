# Independent clock-recovery review

Scope: a separate collaborating executor inspected the timing code and the timestamp fields of the first eight already-sealed singleton training positions. The review did not run a build, Optimize, full matrix scan, or full raw hash pass. It did not read those training arms' U/L values, certificate outcomes, wins/losses, or relative configuration performance. Selection is not reviewed by this note.

The original `round127_campaign.execute` sampled its first-arm tick after wrapper imports and admission hashes. Consequently its inherited `first_arm_includes_wrapper_creation_and_import=true` field overstated that raw receipt's scope. Preserve that receipt and disclose the metadata error.

The existing outer fee source samples `started=time.time()` before launch-record writing and `Popen`, then stores that same value as `PID.json.launched_unix` and `receipt.json.start_unix`. This is a recorded **parent logical production-admission marker**, not an OS wrapper birth timestamp. No unavailable wrapper birth is reconstructed.

For positions 01–08, the reviewer independently checked:

- The PID and fee receipt carry the same start marker and bind to the singleton training group.
- Parent marker <= original arm t0 <= sealed production completion <= verification completion <= fee end.
- Wall-clock versus monotonic elapsed discrepancies are below 0.002 seconds.
- The omitted initial prefixes range from approximately 0.371 to 0.395 seconds.
- No inspected complete parent-marker-to-production interval exceeds its declared cap.

The proposed uniform recovery is valid for all 36 singleton training positions when those bindings, elapsed-time consistency, cap checks, and original nonclock evidence gates pass:

    T_produce_complete = producer_receipt.t_produce_unix
                         - recorded_parent_admission_unix
    T_total_complete   = T_produce_complete + original_monotonic_T_verify

Keep original T_produce/T_verify/T_total and all sealed receipts unchanged. Save the exact endpoint and source-file hashes, raw/corrected clocks, elapsed consistency results, and corrected-cap eligibility in a sidecar used by selection. T_cert is the corrected production time only for an otherwise qualified certified arm; it is null for open or unqualified arms. A cap excess is unqualified, not an ordinary open result and not a cap-imputed certification time.

Applying this same rule to every fixed training position before selection avoids mixing clock origins across configurations. No Optimize rerun is needed solely to repair these observed clocks. The outer fees already include the wrapper lifetime, so the recovered prefix is not added to fees again.

For future raw receipts, the existing `process_origin()` first-arm origin and later-arm ticks sampled before admission checks restore the intended scope without changing the PE, native parameter table, native process limits, mode, input, or prescribed order. This source-level conclusion does not prequalify future results; every corrected complete interval and original scientific gate must still pass.

Disposition: **clock evidence recoverable; first eight inspected positions show no clock/cap blocker.** Final training selection remains pending completion and independent review of all 36 positions.
