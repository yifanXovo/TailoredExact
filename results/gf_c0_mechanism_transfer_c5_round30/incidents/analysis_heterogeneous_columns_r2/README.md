# Post-official analyzer incident: heterogeneous CSV fields

After the arm-aware bound correction, a detailed audit found that the generic
CSV writer inferred its columns from only the first row. The first C0
comparison is legitimately AUC-unavailable, so valid AUC fields in later
trace-complete C0 rows were omitted from the serialized CSV.

This directory retains the affected derived files and analyzer log. Solver
outputs, C5, executable hashes, commands, final bounds, C4/P comparisons, and
the final classification were unaffected.

The general analysis-only correction emits the ordered union of fields across
all rows. A regression fixture covers an unavailable first row followed by an
observed-AUC row. No official process was rerun.
