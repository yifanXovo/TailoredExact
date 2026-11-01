# Independent pre-full review

The non-implementer reviewer `/root/round144_independent_review` inspected the
Round144 source/writer, the new projection primitive, its integration, the
Native readback gate and the two already-solved matched LP pairs. This review
starts no Optimize, compile or commercial Native load. Exact independent
saved-row replay and file identities are in `pre_full_review.json`.

The mathematical direction is correct. For minimization, a >= RN row uses
nonnegative Pi, a <= row uses nonpositive Pi, and an equality permits either
sign. The C++ normalization forms <= rows with nonnegative absolute
multipliers. With aggregate A x + R z <= B, setting submitted extension
coefficients to zero requires B - min(R z); the signed finite-box conversion
formula implements that term and original-coefficient rounding together.
Outward products, sums and coefficient-error intervals provide an upper RHS.
Deleting a coefficient below the Native transport threshold receives the same
signed compensation. Nonzero residual extension coefficients need no exact
floating elimination. The finite production caps are checked against actual
captured bounds, and the existing RN Native audit verifies expected row
directions, scaling and coefficients before they are reused in the projection.

The exact binary64-Fraction replay confirms both serialized diagnostic rows
are valid combinations with their finite boxes and transport compensation.
Reoptimized compact roots retain the measured RN increment to numerical
precision: loss 1.6653e-16 (K35) and 9.9920e-16 (RX20-T1), with no RN columns.
These are numerical optimality observations, not rational optimum proofs.

One lifecycle defect was reported to the implementer before full admission:
the static Round144 attempted/ready/row/input state needs a per-run reset.
The main program supports a files loop, while the inherited main and solver
entry currently reset only R141. Without that repair a second run can carry
old state or fail the old input scope guard. Add a reset preserving only the
enabled option at the run boundary and qualify it before freezing.

Aside from that scoped repair, the inspected source path discards the source
handle and does not merge its bound into formal control. The compact artifact
gets a distinct SHA, row signature and scope. Embedding checks input, g domain,
cutoff and support containment; absent old selectors are identically zero on
the declared narrower support. Formal Native audit requires one exact PC row
and zero RN rows/columns. Default-off gates return before these changes.

Same-root preservation requires an exact optimal dual on the same P and
objective. It is the existing LP-duality principle already identified in R104;
it is neither the entire RN projection nor equal descendant geometry. R104's
negative ACTIVE/SHADOW result and its 4349 auxiliary LP / 3644 DP calls per
method remain relevant history. Arbitrary separate boxes for grouped
multipliers can weaken cancellation and have no automatic root equality.

Expensive full runs remain conditional on the lifecycle fix, actual compiled
C++/Fraction transport checks, Native readback, unchanged complete physical
Start, and a short healthy complete qualifier. Full performance, descendant
loss and a structural distinction from a scalar floor are not established by
this pre-full review.
