# Measured implementation and evidence replay

The predecessor is R168 delivery 2301f9bf0a61d5fe74ee728704a820cb437d5cde.
The measured C++ tree is bound to commit
781c548b410a2749190e3f0c4b149c2ad885c054 and all 254 source-file hashes in
`candidate_manifest.json`. `source_tree_readback.json` checks every byte
against that commit. Later report/reader changes do not alter this C++ tree.

The common full B/M/C executable is `E:/codes/ExactEBRP-work/build-cache/round169/ExactEBRP.exe`,
SHA256 c6ddf0b62f1200d02a8c654fd3f278ced704130f1a8950fc1e6464b9cbb11e57.
It is the full C++ program, distinct from R168's standalone family diagnostic.
The measured Gurobi 13.0.2 DLL SHA is
9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88.
The DLL and license are not distributed. The compiler is MSYS2 GCC 14.2.0,
C++17, Release `-O3 -DNDEBUG`, with no fast-math. Actual configuration,
Ninja commands and compiler identity are in the candidate/environment
manifests and the carrier's build members. Existing runtime dependencies
are identified by the recorded launch PATH, never relabeled as new science.

`h_panel_frozen.json` supplies the exact input hashes, physical parameters,
decimal17/binary64 weights, H seeds and E4 rule. The six R163 inputs have
their inherited source paths; the seventh 6300s R137 role is a different
physical configuration from R163-X35-S. Its recovered input hash is c874...
and the complete inherited physical SHA is in that role's manifest.

The default research mode is off. `--round169-primal-mode multistart` and
`reweight` preserve the parsed R83 preset; `--round169-h-panel` performs the
five-path diagnostic through the same complete H primitive. All complete
commands, including common cap/time-limit/shutdown-margin and Native flags,
are frozen in `matrix_execution_frozen.json` before the first Native call.
Each raw `invocation.json` and `completion.json` binds the actual PE/DLL,
source, argv, process time and return. The full commands contain no historical
or diagnostic incumbent input. Original preset H diagnostics remain base
fields; selected child paths are explicitly recorded in `primal/selection.json`.

The one new-only ZIP and compressed member map are identified in
`evidence_archives.json`. Expand h_raw, complete_raw, qualification and
provenance_revalue under this result directory. Runtime, build and measured
source members have separate top-level prefixes. Compare every member's
length/SHA to the map before using it. Historical H/first-hit members remain
references to their original fixed carrier/member/hash in
`weight_provenance.json`; they are not repackaged or used as new Starts.

The independent standard-library `review/round169_complete_audit.py` checks
actual C++ commit bytes, pure LP/model/Start contracts, Native return/source
quality and whole interval coverage without importing an optimizer. The
separate math and implementation readbacks reconstruct inventories, prefix
loads, compressed travel, returned unloading and G/P/F. Existing successful
checks are retained; this round does not rerun its frozen H/Native experiments.
An independently restored reader environment needs the unchanged repository
source dependencies, not old raw campaigns. Anonymous public byte recovery
is intentionally distinct from a licensed performance rerun.

Build the current maintained R137 paper through the isolated R169 entry:
`scripts/round169_documents.py assemble`, then `pdf`, then `qa`. It inherits
typography, not R168's output/temp/schema identity. Source/build and targeted
changed/adjacent-page visual checks bind the current main and supplement PDFs.
No old figure is regenerated. The B-only CSV increment retains the original
28-column schema and has separate read-only Artifact Tool QA; missing master
data are disclosed rather than reconstructed from expected row counts.
