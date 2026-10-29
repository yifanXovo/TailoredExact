# Independent implementation preflight

Reviewer: `/root/independent_review`, distinct from the primary implementer.
Reviewed the working copies of `include/Round140Research.hpp`, the new
canonical-writer block in `src/CplexBaseline.cpp`, `src/main.cpp`,
`scripts/round140_math.py`, the exporter, and the inherited artifact/epoch
path. No compilation, Optimize or commercial runtime load was performed by
this reviewer.

**Verdict: core arithmetic and integration design pass. Correct the empty-row
edge below and complete the declared actual-matrix qualification before
expensive complete-method runs.** This preflight does not certify the not-yet
reviewed runtime qualification results.

The constructor's common unit is a power of two at least as fine as every
loaded positive binary64 ratio. `frexp`/53-bit mantissa decomposition produces
exact integer units; threshold stock multiplication, coefficient accumulation
and constant accumulation use checked `__int128`. Sorting/deduplication compares
these exact units. Overflow and unsupported conversion throw instead of
silently approximating or merging thresholds. Support validation excludes
empty, unsorted, duplicate and negative inventory states.

The upper construction pays minimum optional increments from the total
minimum-supported inventory, including forced-high stations in the count.
The lower construction uses the largest strictly-low support and sorts the
remaining maximum gains in descending order. Support-budget intersection is
valid. Intersecting the upper budget with total support maxima does not change
the inherited TC count bound: when the physical budget exceeds this maximum,
every optional crossing can already be paid. A failed budget/count domain
emits the established explicit impossible `0 G <= -1` row. It never clamps a
contradictory count interval.

Both the old `(n-u)` and new `(n-ell-u)` accumulations use exact threshold
differences. The new constant accumulates `Delta*ell*u`. Converting each signed
selector coefficient and the constant downward gives an RHS underestimate;
negating the selector coefficient when moving it left is correct. The emitter
retains negative RHS coefficients and the nonzero constant. Positive
power-of-two scaling applies to every row term and the RHS and rejects
nonfinite values. It bypasses the generic writer's omission and near-unit
abbreviation. TC2 emits the old TC row first, preserving the stated inclusion
relationship.

The canonical writer uses the same binary64 `1.0/target[i]` as the original
`r_i-c_iY_i` relation and the model's actual generated inventory-state columns.
Each call recomputes from its current support, so it does not carry a tightened
child-domain row into a larger domain. The main research switch is independent
of stock; it rejects asymmetric placement and other unsupported controllers.
It is fixed for the process. The inherited canonical artifact path serves
outer LP and Native target/terminal, and preserves SHA checks, domain and cutoff
epochs. A new cutoff still invalidates retained Native/LP state. No new column,
Start mapping or ABI change is introduced. With counts off, the added writer
and parameter-persistence branches do not execute; old flags keep their
previous meanings. Byte-level feature-off equivalence remains a qualification
check, not a conclusion from source review alone.

The Python oracle independently expresses thresholds with `Fraction` of the
loaded original ratio-row coefficients and reuses the inherited old-TC
constructor. Its strictly-low bisect convention, sorted gains, constant,
negative slopes and directed rounding agree with the C++ mathematics. Its
infeasibility checks fail before serialization/use; the finite tiny tests cover
a restricted/nonuniform support case as well as the rational witness. Saved
LP point separation is correctly distinguished from a reoptimized objective
increase and from complete-method performance.

Two concrete follow-ups were sent to the primary implementer:

1. For `V=1`, the old TC row can have no `h` terms and no nonzero selector
   terms, for example support `{0,1}` and upper budget `1`. The new emitter
   then prints an empty LHS (`cN: >= 0`). Emit `0 G` when `row.empty()`, as
   the existing generic writer does. This does not affect the declared
   five-role panel, but is a real accepted-input boundary of the new helper.
2. The current exporter persists Native RHS/types/bounds/objective but does
   not retrieve constraint coefficient maps. Actual Native readback must
   also compare TC/TC2 coefficients and the constant, including scaling and
   negative terms. A source-LP/Python comparison alone is insufficient to
   establish Native transport of every small term. This needs no Optimize.

The planned qualification should bind the corrected source and PE to root,
representative child and cutoff-refresh exports, Native coefficients/types,
several integer solutions, and counts-off equivalence. The nine numerical
continuous LP outcomes relayed by the primary implementer have not been
independently integrated or promoted to complete-method claims in this review.

Follow-up closure: the primary implementer added the `row.empty()` / `0 G`
handling. The later independent qualification-plan review rehashed the fixed
source, PE and manifests, reparsed all twelve saved root/child/cutoff-refresh
exports against the exact oracle, and reviewed the recorded actual Native
`getRow`/RHS/type comparisons and their implementation. Both concrete
follow-ups above are therefore closed for admission of the two short
qualification runs. See `qualification_admission.json`; complete-method
performance admission is a separate later decision.
