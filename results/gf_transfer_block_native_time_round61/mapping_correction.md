# Uniform mapping correction before confirmation

The initial fixed120 D6 SUBMIT event rejected the PREFIX snapshot with
`invalid_start_arc`: HGA represents an unused vehicle by a legal [0,0] empty
tour, whereas the complete MIP mapper expects unused vehicles to be omitted.
D6 also uses vehicles 0 and 2 while vehicle 1 is empty; current canonical F0
orders equal-capacity vehicles by nonincreasing service count.

Normalize every PREFIX snapshot by removing empty placeholders and stable
sorting nonempty routes by service count within equal-Q classes, assigning
the available vehicle IDs in ascending order. Never move across different Q.
Current Instance has common T and handling, so these vehicles are physically
interchangeable. Verify the entire before/after witness and inventory equality.
The normalized archive, hash, objective and submitted snapshot stay one object.
This is a mapping correctness fix, not instance-dependent candidate selection.
The constructor remains frozen at initialization +16 generations.

Initial fixed120 D6/D7 SUBMIT rows are pre-correction diagnostics; they cannot
establish effective submission. Repeat D6/D7 OFF/ARCHIVE/SUBMIT at 120 seconds
using the corrected paired build. D3/D4 receive new-build 600-second pairs.
Long/confirmation runs and K1 use that same corrected build. Partial-target
candidate activation is also included before K1 qualification. Optional node
monitoring stops full-vector reads after its three nonroot sample buckets.

Budget adjustment: spend six reserve launches on corrected D6/D7 triples and
two construction-only batches on final D6/D7 telemetry/normalization. Preserve
all three required long comparisons, D4 protection, both confirmations, K1,
same-build references and the oracle/conflict allowance. No confirmation has
been used for selection or this fix.
