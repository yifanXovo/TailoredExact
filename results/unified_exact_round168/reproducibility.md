# Reproducing the bounded C++ route-family diagnostic

Base: verified R167 delivery0da006b442ff7e59a2a63c6700138316611b2ce2,
stacked on `codex/round167-conditional-state`. New executable is
`Round168RouteFamily.exe`, not the historical B/P performance PE.
All outputs/builds/restores/temp paths stay under ExactEBRP-work; the
original repository and dirty paper-current are protected. The tool is
default-off and independent of the full controller.

`candidate_manifest.json` pins actual C++ source, inherited parser/checker/
objective/hash sources, compiler, CMake arguments, PE and licensed DLL.
Configure with `EXACT_EBRP_BUILD_ROUND168_RESEARCH=ON` and local
`GUROBI_ROOT`, build only target `Round168RouteFamily`. The recorded build
uses GNU14.2 UCRT64, C++17, Release/O3 without fast-math, Gurobi13.0.2 C API.
No Python optimizer, generated Python model or old ctypes optimization
core is launched. Python only extracts existing archive bytes, logs
commands, independently recomputes finished data, and typesets documents.

The C++ commands (run in a fresh isolated reproduction root) are:

```text
Round168RouteFamily preflight pool.txt fresh_preflight
Round168RouteFamily tiny-freeze fresh_tiny_frozen
Round168RouteFamily qualification fresh_tiny_frozen fresh_tiny_qualification
Round168RouteFamily campaign pool.txt fresh_preflight fresh_campaign diagnostic_epoch.txt
```

The preflight physically validates18 closed-pool final fleets, freezes
three full-precision targets, tests target members/compatible relabels/
stock embeddings, and registers11 positions. It calls no Optimize.
`tiny-freeze` exhaustively enumerates the two declared physical examples
without a solver. `qualification` checks actual rows for parents, oracle
optima, structural-release and zero-stock witnesses, then runs exactly
six60s-capped MIPs. `campaign` implements the frozen sequence, witness/
same-family skips,300s evidence stops,9-call limit, model construction,
decoding, checking, raw/propagated results and CSV entirely in C++.
Set `diagnostic_epoch.txt` to the enclosing wall-clock Unix epoch just
before qualification. The fresh campaign requires a sibling
`tiny_qualification/qualification_PASS.txt`. The production invocation
uses exactly this sibling name. Do not reuse an old pass marker after
source/input changes. All actual original calls are already completed
or individually accounted in this round; this guide is not permission
to rerun a position to improve its result.

The isolated `tiny-map`, `tiny-solve` and `solve` commands expose the same
functions for a specifically justified repair/reproduction, not a second
budget. Each output directory is exclusive. A failed/started call counts
against its original tiny or family quota. Never delete a partial output
to restart it. Every actual Optimize has a flushed begin/end `call_id`
in `Optimize.jsonl`; parameters, actual model LP, complete Start and
row/type/objective audit, Native log, solution, physical best fleet and
result are retained per call. The callback terminates only on a checked
physical HIT or provisional guarded bound exclusion; final qualification
decides the reported verdict. Requested gaps are zero, Native defaults
and original tolerances remain fixed. Exact cap/readbacks are per call.

Archive recovery uses only final `result.json`/`audit.json` members of the
already-local R163/R164 `new_evidence_01.zip` carriers. Full member paths,
SHA bindings, original complete_arms audit SHA, input and fleet identities
are in `archive_manifest.json`. `scripts/round168_common.py` serializes the
unchanged historical routes as a small text input to C++; it does not
decide physical feasibility or family membership. Original raw remains
referenced by fixed carrier/member/hash, never presented as new evidence.

Document build: `scripts/round168_documents.py assemble`, `pdf`, `qa`.
This is an isolated thin R168 entry inheriting R166/R165 typography;
R167's script is neither run unchanged nor overwritten. R168 owns its
temp, source/build/QA manifests, round identity and author memo links.
The maintained components stay in `results/unified_exact_round137`.
The unchanged three parameter/resource figures and historical tables are
not recalculated. Inspect the changed literature paragraph, route-family
passage/table, citation pages and their neighbors after rendering.

Bound scope is restricted and nonperformance throughout. No L is copied
to B's global ledger; no feasible route or target knowledge is fed into
own-H/AM/Native production. None of the tiny queries, family queries or
archive reevaluations creates a master performance CSV row. Public raw
carriers exclude old raw, private antecedents, commercial DLLs, licenses
and credentials. New source/model/Start/log/fleet bytes are recoverable
through the final science commit and per-member map, recorded separately
from the subsequent delivery receipt.
