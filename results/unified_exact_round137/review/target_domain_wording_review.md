# Independent target-domain wording review

Disposition: **PASS for this documentation clarification**. Separate reviewer
`/root/independent_review` during active arm051. Only small source/document/
metadata excerpts were read; no heavy reader, raw LP/journal replay, optimizer,
build, aggregation, PDF or native asset was used. Only this review was written.
Final120-position/PDF/integrated acceptance remains pending.

The current method source states mathematical D_i>0 and explicitly separates
the computational text format's integer targets and the present data's
D_i<=C_i convention. Appendix A.1 uses the same distinction. The
`round137_documents.references()` replacements preserve that wording when
regenerating maintained sources. They neither add a D<=C physical constraint
nor advertise fractional-target parser support.

Source checks support the distinction:

- `Instance.hpp` stores targets in `vector<int>`.
- `Parser.cpp::namedIntVector` converts numeric literals with llround into
  integers. Station validation requires the resulting target to be positive;
  it does not compare target to capacity. Thus the implementation does not
  preserve arbitrary noninteger D, and prose must not claim that capability
  or claim that every fractional literal is rejected.
- `PhysicalWitnessValidation` validates nonnegative/in-capacity initial stock,
  positive targets and complete physical witnesses through its retained
  validation chain; it imposes no D<=C target check. Inventory/route capacity
  restrictions remain about b/Y and vehicle prefix load, not the aspiration D.

The three current source hashes match `target_domain_wording_check.json`.
Its sixteen base/input-SHA records exactly match the current input manifest,
and all sixteen saved checks report positive integral targets with D<=C.
This review checked those saved bindings, not a new input-generation or native
experiment. No empirical claim for noninteger targets or D>C test performance
has been added.

No inspected Appendix derivation needs D<=C beyond describing the tested data:
ratio/Gini definitions and the nonnegative-ratio bound require D>0; the ratio
upper bound C/D remains valid; the deviation bound max(1,C/D-1) also covers
D>C; finite inventory states and implicit quantity integrality depend on
integer b/Y and service direction, not target-capacity ordering. Penalty
domain inversion, the shortage floor, state/objective embedding and resource
validity similarly use positive D with the stated separate premises. If a
target lies above capacity, Y=D may simply be unattainable; that does not
invalidate the stated zero-objective equivalence or add physical feasibility.

The correction is faithful to the original feasible problem and actual
integer-storage implementation. No source/PE/input/frozen matrix change or
additional qualification run is warranted by this wording-only correction.
