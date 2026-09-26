# Runner review and limited D6 diagnostic admission

The coordinator independently reviewed both runner sources, reused readers, final fixes and preparation evidence on 2026-09-26. Reviewed SHA256: `round88_a1_g3.py` = `178e83fcb56143109d00f407af770b711a7e69c5816e63a0aa094dee8ff3eadd`; `round88_startup_diagnostic.py` = `d218f400000c82947df38d9a32830598a96e6ec94f004fedde9d8cee48eb5f0f`.

The review identified and resolved an actual `input_path`/`instance_path` interface mismatch before execution. Historical D6 physical/construction/closure replay now passes on the frozen reader version. P model SHA checking, dependency identities, cross-arm bound contradictions, failed-attempt accounting, process-exit versus post-exit audit timing, and whole-run-only deadlines were also checked. The preserved D7 compact export's SHA matches its registered reference, confirming the byte-level identity convention used here. No experimental result has been used to adjust a threshold or algorithm.

Latest local runner session metadata was inspected immediately before admission: `gpt-6-sol`, effort `high`, cwd `E:/codes/ExactEBRP`. This verifies the local request/runtime record, not hidden provider routing. The host process inventory showed no active experiment/build/OT process at that check.

Decision: authorize **only the two preregistered D6 startup diagnostics**, on the qualified A1 binary and identity `c6c32d1fdc8b142230a951139c516629a72f6b97111fa4ca291ae1f5f45d1941`. Both arms execute the full startup and physical closure, require zero Optimize and preserve all original evidence. These are mechanism diagnostics, not complete exact-method timing results. Resource ownership belongs to Sol-Runner until both processes and their offline audits finish. Other workers may perform light source review only during that interval.

G3 remains pending. E8/S12 can receive a separate lease after reviewing D6 and the final independent runner findings; the remaining six roles require the explicit smoke gate. No mainline promotion or large long-run campaign is admitted here.

## Subsequent E8/S12 smoke admission

D6 completed normally with both independent audits passing: ENS-C startup 6.078 seconds, physical UB 0.15750980361456166; A1 startup 0.297 seconds, physical UB 0.17161162683007503. Both fully exhausted their declared startup/closure and performed zero Optimize. Total process cost was 6.375 seconds, with 0.469 seconds of host prelaunch checks and approximately 0.176207 seconds of offline replay separately recorded. The weaker A1 UB is retained as negative evidence. It does not establish complete-method performance either way and does not justify promotion.

Sol xhigh independently read the final G3 runner hash above and found no new blocker for the six E8/S12 arms. Root accepts that review and authorizes this limited smoke phase, contingent on the OT worker releasing the shared computation slot after its in-progress qualification. The runner must obtain that confirmation before launch. No additional heavy validation/build/solver may overlap. All six arms follow the frozen manifest, with the existing audit and severe-risk stops. No remaining G3 arm is authorized by this smoke lease.
