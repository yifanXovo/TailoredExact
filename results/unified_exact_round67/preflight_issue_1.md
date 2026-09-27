# Inherited zero-handling reachability defect

The first Round67 model test failed with "unexpected propagated domain size"
(CTest0.12s). This occurred before any Round67 performance or native-micro
experiment. The initial build succeeded in66.804s; build/round67/build.log and
build_status.json retain that build attempt.

Both CplexBaseline.cpp's local domain calculation and IntervalRowFactory.cpp's
shared calculation initialized station movement to zero and only changed it
when c_pick+c_drop>1e-12. Consequently zero handling fixed inventories to their
initial values even when travel permitted a visit and the vehicle had capacity.
The CLI admits zero service times; this is an inherited semantics defect, not a
failed encoding theorem or a legitimate propagation strengthening.

The repair uses the vehicle's Q bound when handling is zero, provided the travel
lower bound is within T. For positive handling, cap the floored time-based
movement by Q before integer conversion. The subsequent min(initial/room,Q,
movement) gives exactly the old positive-handling domain while avoiding an
unnecessary potentially overflowing conversion. No certificate tolerance changes.

The same correction is applied to both row-factory paths. Zero handling belongs
in the model/domain test and will receive a separate native original-problem
check before performance. The new stage uses fresh P-GRB and K1-R references.
Round66's positive-handling performance observations are not rewritten; its
load-replacement equivalence proof remains a component proof, not a cure for
preexisting domain errors in retained blocks.

Broader retained-cut assumptions also require care: direct depot round-trip
distances are lower bounds under the supplied Euclidean/metric travel data,
but not for arbitrary nonmetric matrices. This is an open applicability audit.
Do not claim that the complete strengthened controller is already qualified for
all nonmetric input matrices merely because a replacement block is valid there.

The new Round67 presets now check finite, nonnegative, symmetric metric travel
before HGA or optimization and reject unsupported matrices explicitly. The
existing presets and official P-GRB are not silently routed to another method.
The next full CTest pass ran44 tests in4.38s:43 passed and the new test failed
only because its textual assertion expected explicit coefficient1, whereas the
LP writer omits unit coefficients. Inspection found the correct offset-code
equations. The assertion was corrected to check both exact rows; no formulation
change was needed for this second failure. Both failures precede all native
experiments and are retained here rather than counted as valid performance.
