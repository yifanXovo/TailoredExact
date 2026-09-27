# Round72: short certification gains; long protection test incomplete

DS-X recovers D3 certification and materially accelerates C2 relative to DS,
while retaining D4's advantage over official P-GRB. The unchanged candidate
passes the nine-run short panel. The first admitted D7 long run, official
P-GRB, was killed by the supervisor after failing to return within its deadline.
It has no retained physical endpoint. K1-R and DS-X long arms never launched.
The stage is complete as mixed validation evidence; the overall goal is unmet.

Base: Round71 final73ce04d9a3c5031c2b5a1021523502f0a9a85168, draft PR132.
This stage: codex/round72-vdsx-validation, draft PR133:
https://github.com/yifanXovo/TailoredExact/pull/133 . No main merge.
Compiled source3867214f480d0a4fef4d77f03404f9fd89fb8b42 and executable
4f60ed8cd6f65c695947e8ac3bd525b77d28d94733faf2c9ef25d057a69023af
are inherited unchanged. No new build or test execution is implied.

## Credible performance result

All three arms have common300s process caps and pay startup, model/probe work,
native proof, verification and exit. Original Gurobi13.0.2, Threads1, Seed0,
PresolveAuto, requested gaps0 and numerical tolerances are preserved; all
fresh arms use the same mask4 with readback and restoration.

|Role|Official P-GRB|DS|DS-X|
|---|---|---|---|
|D3|Open U0.045054162 / L0.041517822|Open U0.045001550 / L0.043228707|Certified255.360s|
|C2|Open U0.829963413 / L0.771482134|Certified154.219s|Certified111.234s|
|D4|Open U0.506343308 / L0.196073312|Certified53.860s|Certified54.703s|

D3 regains the certificate DS lost. C2 saves42.985s/27.87% against DS, passing
the frozen material threshold. D4's0.843s difference is below that threshold,
without a statistical-equivalence claim. Full precision endpoints and pairs
are in campaign/short_runs.csv and short_pairs.csv. The previously audited
campaign/runs.csv, pairs.csv and their nine-run QA remain unchanged.
short_validation.md is the historical pre-long checkpoint, not final status.

Six separate startup-only diagnoses also pass. Each full candidate run pays
for and independently reproduces its diagnostic initial route and logical
descent trace; no route is imported. Cross-route acceptance is observed on
all three roles. Better startup U does not uniformly accelerate proof: D4
has no material full-time difference. This does not establish long-route
protection or independent generalization. See algorithm.md and mathematics.

## Failed long run and evidence boundary

The predeclared gate admitted exactly D7 P-GRB/K1-R/DS-X3600s. Run10 P-GRB
entered one native Optimize call at process0.3268263s. Its effective native
TimeLimit was3596.6733358s. Original compact fingerprint0xe9c08735 matches
the independent no-opt export:35618rows/13360columns/176870nonzeros.
The final recorded native progress line is3592s. No native time-limit summary,
Optimize return, result.json or final physical route was written before the
supervisor killed PID8404 at3610.063s. The Python queue then exited1 and did
not launch the other two arms. No restart was performed.

The process did not meet its3600s contract. Approximate log incumbent and
bound are diagnostic telemetry only: formal UB/LB/gap remain unavailable.
No old/future witness is spliced in. The attempt contributes one failure,
one native call and all3610.063s to costs. The exact native reason for delayed
return is not established.

Source inspection finds the reliability defect: GurobiBaseline.cpp buffers
progress in memory, then extracts/verifies the solution and writes progress
only after synchronous Optimize returns. The official TimeLimit documentation
allows extra native work after the limit; GRBterminate is also a request
without an immediate-return guarantee. Thus the existing fixed shutdown
reserve is not a general guarantee. This does not establish the internal
cause of this particular native delay.
[TimeLimit](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#parameter:TimeLimit),
[GRBterminate](https://docs.gurobi.com/projects/optimizer/en/current/reference/c/callback.html#c.GRBterminate).

long_failure.json, attempts.csv and failure_manifest.json retain all15 compact
lossless artifacts for the failed run and D7 reference export, including
model, command, native log, phase and affinity evidence. Original raw files
remain local. Added artifacts total1044691bytes, decompressed and checked
against6310594 original bytes. No valid long endpoint is claimed.

## Acceptance and resources

The nine short runs passed22 retained witness/model checks,11 accepted and
fully observed native Starts, full-domain coverage and numerical consistency.
Three original P controls have no added Start.159 short-run artifacts and
all source/input bindings were rechecked at closure without altering the gate.
The six diagnoses retain48 further artifacts. Independent replay of retained
Start/readback vectors is distinguished from the C++ observer's unretained
full native event vectors. Certification retains original numerical tolerances;
it is not strict rational certification.

Actual total:16 experimental attempts =6 diagnoses +9 valid short runs +1
failed long run;5428.095s and37 native Optimize calls. Four separate no-opt
exports cost0.516s.49 CTests and39 qualification calls are inherited from
Round71; newly executed counts are0. The earlier offline packaging schema
failure remains in postprocess_failures.json. Closure verification costs
2.090s separately; all solver attempts retain full process costs.

Default-off DS-X remains admissible: finite decoded descent produces only
independently verified physical UBs and leaves complete proof coverage intact.
This stage establishes useful nonzero proof improvements, but R71's serious
D7 K1-protection loss remains unresolved. No current long comparison, broader
confirmation, new-theory claim or overall success is asserted. The original
dirty checkout and stable defaults remain untouched.

## Next work

Do not reopen or repeat this stage. Before another long comparison, qualify
durable physical-witness and full-domain/frontier evidence under whole-run
termination, including forced termination and incomplete writes. Apply
equivalent measurement semantics to P and candidates and bind fresh controls
if shared instrumentation changes. Do not change P's search settings or add
time-sliced fallback.

The next optimization hypothesis is direct joint route insertion with integer
pickup/drop quantities, described prospectively in prospective_primal_note.md.
It targets D7 primal-quality debt with explicit load/time feasibility and
original-objective scoring. The note is not an implemented or validated
mechanism. Any experiments require a new bounded plan and identity.
