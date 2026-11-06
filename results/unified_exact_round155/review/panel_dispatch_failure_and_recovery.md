# Observed pre-Native dispatch failure and bounded recovery

NB35 E7200 completed normally and passed its complete original-problem
verification. Its physical U is .4297444110493129, raw search L
.39074482582731757 and supported proof L .3959564087240911. The paid outer
fee is 7183.030154600041 seconds; T_produce=7171.765302203596,
T_verify=11.188206800026819 and T_total=7182.9535090036225. It is uncertified
and T_cert is null. The raw search lower and physical upper agree with B;
the independent floor still improves the supported lower at this endpoint.
Full-panel and checkpoint interpretation remain pending.

The following confirmation_003 attempt failed before creating its producer
destination or starting Native. Its 1.938000899972394-second outer receipt
has exit_code=1, exit_observed=true and timeout=false. The unchanged
round100_idle.ensure_idle guard rejected the independently waiting
round155_followthrough.py process as a foreign optimization process. The
primary queue stopped immediately; the waiting queue then stopped on its
predecessor's failure. No readback or remaining deep job was started.

The failure logs, receipt and both failed queue identities/status files are
retained. Actual OS readback found the recorded Native process, both queue
processes and the reported foreign launcher gone after the failure. This
is a dispatch/idle-admission problem, not a solver, mathematical-interface
or candidate-E failure. The earlier NB35 run was already launched before
the independent waiting dispatcher was created.

Source inspection of round90_lp_g_g3.foreign_heavy_processes confirmed the
precise trigger: its Python command-line pattern includes round88[_-]ot.
The reused interpreter's path therefore matches even for a Python process
that is merely waiting. The idle guard excludes the current job's actual
ancestors, not arbitrary independent observers. Keep this guard unchanged;
use PowerShell file/status and OS process-birth reads while timed work is
active, and do not start a separate Python waiter or Python status observer
through that interpreter. This observation policy changes no solver rule.

Recovery uses one owner for the two remaining complete arms. It calls the
unchanged round155_campaign.py arm entrypoint with the original frozen
matrix and destinations, unchanged own-H/floor behavior, PE and parameters.
The original idle guard remains active. Position3 receives the fresh outer
label confirmation_003_retry_v1; its failed original label is never reused.
Position4 retains its never-started confirmation_004 label. Destination
nonexistence is checked before either launch, so no prior producer evidence
is overwritten. Each arm retains a full 7200-second allowance and its own
verification. A failure stops the new owner without another implicit retry.

The recovery admission and actual future execution must be assessed through
their own saved receipts and source snapshots. No independent waiting
dispatcher may be started beside this owner. After all six arms actually
pass, panel_completion.json will bind each accepted endpoint/closeout to its
real paid attempt, while retaining the failed preflight fee separately.
The post-panel research continuation must use that concrete completion
evidence; the old failed queue status must never be relabelled as success.

The actual panel_recovery_admission_v1 passed with a 1.3290115999989212-second
verification fee. The sole recovery owner started at UTC2026-11-05T23:52:10
(PID88688); confirmation_003_retry_v1 started at23:52:11 (PID90064), and
the actual Native process21496 was confirmed alive with its recorded birth.
No production or idle-guard source was edited. Dispatch receipt/hash
bookkeeping is lightweight orchestration; the full per-arm verification
remains inside each paid child lifecycle.

The unexecuted prepare_closed entrypoint in round155_followthrough.py now
requires the recovery owner to have exited and all six accepted endpoints
to bind to successful actual receipts. It preserves the unused nine initial
readback/support/admission jobs and all subsequent research rules from the
old plan. round155_deepen.py now checks the six-arm completion and attempt
bindings instead of the old failed queue's terminal state. Both edits concern
orchestration admission only and have passed syntax checks; their actual
post-panel execution and the remaining research checks are still pending.
