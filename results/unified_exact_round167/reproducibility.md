# Reproducing the offline conditional representation

Start from the verified R166 delivery d497052216d5ae55b6ae0139ea30910cee2e5865
and the new source/publication pin recorded in the separate delivery receipt.
All new files, builds, raw and temporary files stay under ExactEBRP-work.
The original and paper-current worktrees remain protected. C166/B's old
measured executable is not used as the new diagnostic executable or relabeled.

`candidate_manifest.json` gives the actual GNU14.2 compiler, full CMake
configure/build argument arrays, new PE and Gurobi13.0.2 DLL SHA. Enable
`EXACT_EBRP_ENABLE_GUROBI=ON`,
`EXACT_EBRP_BUILD_ROUND167_RESEARCH=ON`, set the licensed local GUROBI_ROOT,
and build only `Round167Research`. The option is default off. The new entry
neither changes main's method nor implements a new complete controller.
Use the bundled/licensed external Gurobi installation; commercial runtime
DLLs and licenses are not published.

The C++ commands are:

```text
Round167Research algebra output.json
Round167Research tiny-oracle output.csv
Round167Research local-prepare L1|L2|L3|L4 R_abs|C166|D167 new_output_directory
Round167Research prepare input T lambda parent new_output_directory B|C166|R_abs|D167 alpha beta cutoff condition_level S0
Round167Research solve prepared_directory LP|MIP time_limit
```

Pickup/drop times are fixed at 60s for these exact inherited frames. Other
extension options are not accepted. Prepare emits the base/final LP, exact
common blocks, per-station graph sizes and, when legal in the scope, a
complete actual-column Start with all rows/bounds/types/objective checked.
R_abs selectors are continuous; both new representations use integer
absolute delta for tiny MIP. D167 compiles its graph directly from bounds;
the temporary B physical carrier still has one-hot preparation/storage cost.
Its final logarithmic representation is not a logarithmic full writer.

`scripts/round167_diagnostics.py preflight`, `boundaries`, `freeze`, `execute`
and `summarize` are the exact orchestration actions used. They import no
solver. Preflight prepares every model and mask with zero Optimize. Freeze
creates the immutable `diagnostic_manifest.json` before the first Optimize,
binding all 88 positions, inputs, exact inherited argv, matrices, objective,
scope/cutoff, source, PE, parameters and caps. Execute is serial and refuses
duplicate solved directories or changed frozen source/PE/model bytes.
Replications require a separately named output root and explicit new
experiment accounting; do not rerun healthy historical positions in place.

The first solver-free preparation PE/source is preserved separately in
`build/preparation_v1.zip/json`. Before any Optimize, the final source guards
INT_MAX singleton receiver construction and adds parameter/dual evidence;
this does not change any prepared mathematical frame. All 88 Optimize calls
use the final measured PE. The raw models have individual immutable SHA,
and sixteen R166 original canonical base exports match byte-for-byte with
zero new solver calls. All B/C166 production writer/backend/Start/factory
sources remain unchanged.

`positions.json/csv` reports every position. Raw LPs relax every integer
type and retain primal/dual reduced-cost evidence; original types are
restored. Tiny MIPs restore those original physical types, retain their
new code binaries and use a physically verified Start. The finite C++ oracle
and independent offline row/KKT/route checks are in qualification/review.
No tree, callback or opaque Native state is reused. Purely independent
reviews add zero Optimize and their actual/failed computation fees are
separately included in `cost_report.json`.

R_abs/D167 common hashes agree. C166's B20 root/child raw hash additionally
classifies ten singleton-initial V=0 equations as common because those
representation links contain no auxiliary coefficient after degeneration.
The independent review verifies every such station and normalizes those
links; all eight physical interfaces agree. Raw identities remain visible
and are not overwritten with normalized hashes.

For the documents, run the current component-only entry `round167_documents.py`
with actions `assemble`, `pdf`, `qa`. It explicitly inherits R166/R165
typography and binds date/toolchain/templates. No old R137 prose generator
or R166 parameter/resource recomputation is run. The one current manuscript,
main plus complete appendices PDF and supplement PDF are under R137.

New-only raw carriers and member hashes are identified in
`evidence_archives.json`; fixed predecessor sources/carriers are referenced,
not downloaded or repackaged wholesale. Public recovery checks only this
round's changes. The exact science commit and later receipt commit are
separate; no artifact claims its own not-yet-existing commit SHA.
