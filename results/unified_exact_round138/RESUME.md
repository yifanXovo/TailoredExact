# Round138 continuation

User requested strict execution of `goal.md` A-J. Goal remains ACTIVE until
science, manuscript increment, independent final review, English Draft PR,
finite public byte recovery and bounded current-round cleanup are complete.

- Use `E:/codes/ExactEBRP-work/worktrees/paper-current` explicitly. Original
  `E:/codes/ExactEBRP` is protected. WORKSPACE_POLICY conventions inherited.
- Branch: `codex/round138-shared-product-resource-coupling`, based on accepted
  R137 `72fdcd31716d7b4798727b4ea964b32059c630d1`. main is still
  `b2b940c1e517a72e226ec60fc49ff19651737632`; PR base must be R137 branch.
- Production/source pin: `839283773` (full hash in candidate_manifest.json).
  Default-off CLI `--round138-stock-rlt`, exactly four stock product rows,
  no extra variables. R137 entry/config/PE remain intact. Candidate PE in
  `E:/codes/ExactEBRP-work/build-cache/round138/ExactEBRP.exe`.
- New solve budget: 86400 s total. Actual fee ledger uses
  `scripts/round138_common.py budget`; nested H/LP/MIP not added twice.
  All new unqualified experiments Seed0; only explicit limited repeats Seed1.
  Full own H seed remains 20260626. Single thread, affinity4, serial.
- New runtime: `D:/msys64/ucrt64/bin/python.exe` for scripts; Python LP runtime
  `E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe`,
  Gurobi13.0.2 bound to `D:/gurobi1302/win64/bin/gurobi130.dll`.

Completed: actual refs/idle processes/policy checked; mathematical/history
review and exact J2/J3 four-cell replay; heterogeneous product counterexample;
four R137 saved roots including three specified points; seven-domain actual
default-off matrix bridge and exact four-row/full-precision/RHS checks;
20 preregistered same-domain LPs, all OPTIMAL. See roots/*/result.json,
math/exact.json and review/{pre_math,pre_implementation,LP_admission}.md.

Stock LP increments over newly reoptimized base: K35 +.0179111171,
RX20 +.0459632140, RX35T2 +.0070363188, K20 +.0094412867.
TC+stock adds further information on K20/RX35. Main full candidate is uniformly
stock-only (minimum four rows), AP/TC off. GS controls were independent and
shared aggregate envelopes on K35/RX20, with justified same-domain S bounds.

Three offline preparation bugs/corrections are disclosed in
infra/preflight_corrections.json. In particular initial RX20 stock export used
a recomputed U differing from native cutoff by one ULP; exact matrix comparison
refused it before Optimize. That export is preserved. Corrected exports reuse
the original stored beta/native cutoff and differ from each saved matrix only
by four rows. Gap denominators still use the independently validated U.

Full plan: experiment_plan.json and matrix_frozen.json. Eight physical/objective
configurations / six base inputs / 16 nominal core method positions; eight
strictly matched accepted R137 baselines reused, eight new STOCK runs. Also
one contemporaneous K15 frozen-PE BASE bridge and two 90s micro runs, total11
new positions. Independent reviewer must write full_admission.json with exact
matrix SHA and ACCEPT before run. Pilot is positions1-4; do not launch duplicate
healthy processes or overwrite failed evidence. `round138_campaign.py run 4`
executes pilot, later `run 11` completes remaining entered panel. Every run
uses inherited complete producer, physical/H/Start/certificate reader, plus
actual new stock rows audited in every used model. Baseline full costs were
paid independently in R137 and are not newly charged.

Update 2026-10-29 02:14 Asia/Shanghai: full admission ACCEPT. Position1 BASE
native returned OPTIMAL and was sealed; its first postreader incorrectly used
legacy rather than modern event ordering for `baseline-r137`. Original failed
fee/log retained; no native rerun. Strict modern lifecycle private namespace
and the narrow two-helper amendment were independently reviewed (including
three negative controls) and accepted in review/reader_amendment.json. Original
matrix bytes remain unchanged. Only verification was resumed under engineering
fee arm_001_verify02; it passed. Formal T_produce=122.57938176719472s; U and L
match R137. Failed native fee charged the original producer once. The next
`run 4` skips sealed/qualified position1 and starts positions2-4. Current active
session identity/PID and fee files determine progress; never restart a healthy
running position. Production source/PE, solve commands and original policy
were unchanged by this postreader correction.

Independent reviewer agent is `/root/independent_review`; user goal H explicitly
authorizes this delegation. It has completed math/static/LP admission reviews
and is reviewing the frozen full matrix. Use collaboration followup, not app
thread tools. No other agents required.

Remaining: full pilot and justified completion; finite Seed1 selected on actual
results (max two roles paired); optional resource exploration only if informative;
aggregate U/L/certificates/times/trajectories, explicit research decision;
paper increment in current R137 lineage and affected-page PDF QA; source/raw
carriers/portable pure reader, final independent review; normal push and English
Draft PR (no merge/force push), attach PR; bounded public new-carrier read and
current-round cleanup/retention receipt. Preserve R137 historical recovery
limitations, do not reopen all historical recovery or delete old rounds.

PDF skill has been read; before the first PDF authoring command, run the bundled
mark_artifact_operation_started.mjs once. Use existing document assembly rather
than old Manuscript sources; keep R137 complete manuscript unchanged. No PDF
export, build or heavy I/O during timed formal solves.
