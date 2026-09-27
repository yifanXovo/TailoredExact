## Problem and proposed change

The fixed Round91 canonical-LP diagnostic found a processing-capacity relaxation gap on C2: its numerical original-F bound rose from 0.60266647 to 0.62264258 with two rounded travel/activation rows. D3 showed no objective gain. This PR prepares one uniform static row family for a later full-method test, without claiming that a root-bound gain makes MIP faster.

For each vehicle, the proposed row bounds total integer pickup by a proved processing allowance times binary depot activation. A directed shortest-route lower bound uses the same coefficients as the original canonical duration row. The pure helper computes outward numerical bounds and rounds the reliable quotient upper bound down to an integer; ambiguous exact-floor equality yields a conservative valid row, rather than a retry or an instance-specific algorithm choice. The design covers zero handling, no closed route, loaded return, coefficient serialization and unsupported arithmetic.

## Status and validation

This is **unlinked, unbuilt source preparation**: helper, header, pure correctness-test source, design and unapplied integration instructions. No existing qualified source, CMake target, CLI, preset or frozen Round90 executable is changed. No test, model export or Optimize has run for Round92.

The [independent static review](results/unified_exact_round92/handling_activation_independent_static_review.md) conditionally accepts the pure kernel and states the required actual-model, arithmetic and physical-validity checks before integration can be qualified. The [plan](results/unified_exact_round92/plan.md) allows only one candidate and a finite subsequent screen. Default-off identity, exact coefficient/cache correspondence, unchanged original tolerances and complete costs remain required.

R7/R8/R63 related constraints and negative performance evidence are retained. This is an application of known rounding/activation reasoning, not a new general inequality theorem or a full routing-model convex hull. The separate Round90 G4 batch continues to own computation; there is no promotion or long campaign here.
