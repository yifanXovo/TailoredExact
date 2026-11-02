# Round146 independent production static review

Reviewer: `gd_independent_review`, not the primary implementer. Reviewed the
first production implementation in `include/Round146Research.hpp` and its
changes in `src/PaperExternalGiniTree.cpp`, `src/GurobiBaseline.cpp`, and
`src/main.cpp`; also read the row driver and incremental build script. This is
a source review, not a claimed compiled execution or Native qualification.

Status: **PASS for the reviewed mathematics and static wiring, with runtime
qualification still required before expensive complete runs.** No code changes
were made by this reviewer. No Optimize, compilation, or Native load occurred.

The block builder validates sorted distinct nonnegative supports and finite
nonnegative c. Exact checked dyadic numerator and denominator sums are reused
from R140. The continuous-box fill sorts by actual c and fixes the selected
state by zeroing its remaining capacity. Exact conditional-bound nesting is
checked before conversion. The minimum/maximum targets use physical inventory
totals, and no discrete-support extremum is claimed.

For a nonzero exact numerator, upward numerator/downward lower denominator
followed by upward quotient and downward subtraction gives a safe low
coefficient. Downward numerator/upward upper denominator followed by downward
quotient and subtraction gives a safe high coefficient. `max(0, ...)` preserves
safety. Exact zero numerator gives low coefficient 1. Tiny positive terms are
omitted only on the selector side, which weakens `n G - sum a*s >= 0` because
s>=0. An infeasible conditional state gets zero terms; a nonpositive whole-domain
S lower bound omits the entire mechanism. Nonminimal g starts remain valid.

The production embed path generates coefficients once per solve, records
generation time and applicability, and checks the input file hash, actual
ratios, inventory bounds and support containment on later embeds. It retains
the root coefficients and deletes only selector terms absent in a sub-support.
It neither claims nor needs renewed optimality or a new source solve. Inputs or
support expansion are rejected. `round146ResetRun` preserves the flag and clears
the per-run cache. The expected-row map binds actual canonical model hashes.

The call is placed after canonical model construction in `ensureArtifact`,
which is shared by the stable initial LP, target calls, child LPs and terminal
MIPs. It adds zero variables and at most two rows through the existing canonical
append routine. Native audit checks the fingerprint registration, absence of
RN columns, row count, exact coefficients, RHS and senses. The command-line
flag defaults off; enabled mode is restricted to the intended stable ms2 carrier
with optional BOTH STOCK. The supported frozen configuration does not admit
the competing RN/projection/count-proof branches. Unsupported combinations
must not be presented as qualified.

The new header is included by exactly the three changed production translation
units listed in `round146_build.py`: GurobiBaseline, PaperExternalGiniTree and
main. Their old objects are replaced; unchanged objects/libraries are hash
checked. The measured build still needs its resulting source/PE identity and
runtime evidence. A standalone header-driver compile is not a substitute for
that full link.

Remaining admission evidence is deliberately narrow: exact-oracle comparison
of actual emitted rows; default-off old-matrix equality; a strict sub-support
inheritance case plus expanded/changed-scope rejection; actual Native sign/NZ
readback; physical Start with nonminimal g; and one short complete health run
covering formal models and inherited proof/lifecycle verification. The finite
LP evidence then decides whether and how to enter the same-PE K20 strong-reference
experiment. This review does not assert performance or candidate promotion.
