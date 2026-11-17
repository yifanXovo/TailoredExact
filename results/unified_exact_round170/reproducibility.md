# Reproduction and evidence ownership

The measured algorithm source is 781c548b410a2749190e3f0c4b149c2ad885c054.
R170 changes no C++ file. `candidate_manifest.json` records actual common
PE/DLL/compiler/build hashes, and `source_tree_readback.json` records the
254-file comparison with the measured tree. The measured PE is reused, not
rebuilt or renamed. The commercial DLL and licenses are not distributed.

Use a new authorized workspace under ExactEBRP-work, the recorded compatible
Windows/Gurobi runtime, and the immutable R163 inputs. `round170_common.py`
records a fresh entry; `round170_run.py freeze` writes all actual commands;
commit that matrix before `round170_run.py complete`. Production is strictly
serial, pinned to affinity mask 4, with Threads/MIPThreads 1. The process cap
is 600s, work deadline 594s, shutdown margin 6s, with a 602s outer safety
boundary. This does not grant each child another 594s: actual child requests
come from remaining shared time. No new H-only qualification is required.

Run orchestration with the bundled Python executable explicitly; the local
WindowsApps python alias is inactive. Each complete_raw directory is created
once. Its invocation binds actual argv/PE/DLL; completion binds return code,
process outer clock and returned result bytes. Existing incomplete or failed
positions require inspection rather than automatic optimization reruns.

`round170_audit.py` adapts R169's standard-library pure journal, physical,
model, actual log, Start and complete-cover reader to Native Seeds 1/2 and
the new runner receipts. It checks every actual Optimize's parameters. P has
one full-original compact model and actual NumStart=0; its qualified original
bound is handled separately from the tailored interval cover. Neither
cross-arm bound maxima nor cross-arm incumbent minima define an endpoint.
`round170_results.py` consumes only passing audited rows, preserving full
binary64 objectives and separate process/audit clocks. It emits four separate
comparison files and the B-only 28-column increment. R170 M/P have Seed1
only. Historical Seed0 remains explicitly R169 and is not a missing control.

The complete-arm H reader requires the actual one/three completed valid paths;
selection.necessary_H_complete is only the five-path diagnostic gate.
Random-order identity is SHA256 of the LF semantic transcript; raw Windows
text files additionally have their own byte hashes. Every new fixed H is
compared read-only with R169's terminal metadata. Those old files never enter
production argv or any Start. First global discovery times are not identified
by buffered/rounded solver logs and remain missing.

Historical compact qualification is recoverable from fixed commit
f7083ace21ad2a8bd54bed71711ceebcb97c9e8c,
results/unified_exact_round163/artifacts/new_evidence_01.zip,
members results/unified_exact_round163/qualification/references/<role>/
build.json and original.lp. Exact inherited member hashes are retained in
R164 qualification/inherited_references.json. R169 metadata and raw evidence
are pinned to delivery ff77c4e18985a55370d58a2b2731a51566a07eb8 and its
evidence_archives.json/member map. No historical raw collection is repackaged.

The user-specified 118-row base requires SHA256
5e3303adfba0092c465b8dab3232e1ced7d0e85d8d21aa3e8398ed0d3e5880e3.
It is absent from the bounded attachment lookup. Older 91/103-row CSVs are
protected and cannot replace it. The eight-row R170 increment can be appended
after checking that base, retaining every historical byte and rejecting
duplicate input/Seed/Round/cap keys. Only three n35 Seed1 B rows have new P;
five other B rows explicitly remain N/A-P. C/M belong to candidate files.

The maintained manuscript authority stays results/unified_exact_round137.
Use the thin `round170_documents.py assemble`, `pdf`, then `qa` entry points,
with R170 output/temp identities; inspect actual changed/adjacent rendered
pages before accepting PDF hashes. This process rebuilds no experiment or
historical figure. The final delivery packages only new raw once, verifies
all archive members, and performs public byte recovery at a real pinned
science commit. Subsequent delivery receipts never claim a future self-SHA.
