# Round125 independent review — Stage 1 (document only)

Reviewer role: independent_methods_review. Date: 2026-10-18.

Scope: only manuscript.md, model_appendix.md and algorithm_appendix.md were read before this report was saved. No specification matrix, production source, prior readiness label, solver output, or other review was consulted. No solver, LP/MIP/CP/DP optimization, production compilation, or H search was executed.

## Assessment before source access

The three documents now specify a coherent mathematical method in substantially more detail than an architectural outline. A reader can reconstruct the physical model, inventory selectors, implicit integer service argument, tight physical auxiliary embedding, static cut coefficients, midpoint cover and principal NEXT/AM decisions. The numerical closure exception is disclosed explicitly, so the exact mathematical embedding theorem must not be applied literally to that implemented impossible-row guard. Physical neutral moves use exact recomputed objective equality and the full descending duration vector. H distinguishes order encoding from physical routes and exposes the active greedy/compensating decoder.

No foundational contradiction in the ideal physical/cut/cover arguments was found in this first pass. Source fidelity has not yet been assessed.

## Findings to resolve or delimit

1. **S1-01, certificate policy incomplete for a standalone executor (medium).** Manuscript Algorithm 1, Section 5.4, A.7 and B.4 repeatedly invoke the inherited signed-gap test, consistency gates, and zero-evidence policy without writing their exact predicates. The tolerances are stated, but a reader cannot determine whether a negative signed gap of -2e-7 is rejected, capped, source-reduced, or certified, nor reconstruct the complete nonzero/own-zero admission decision from the three documents alone. Add the explicit numerical predicates and operational qualification gates, or limit the self-contained claim to model/controller generation while identifying an external, immutable certificate policy.

2. **S1-02, equivalent-key H decisions remain a declared reproduction limitation (medium).** B.9 says eight atoms/six local candidates are retained by bounded heaps with EPS logic, while B.10 explicitly acknowledges nonstable objective-only sorting. This describes the mathematical neighborhood and admission criteria but does not uniquely specify retained equal-score candidates or cross-library path-level output. The frozen compiler SHA alone does not explain the heap replacement predicate. Record the comparator/replacement rule, traversal order, and exact library/binary dependency. An explicit acknowledgment that portable reimplementation can follow a different valid H path is appropriate; inventing a new tie rule would be inappropriate.

3. **S1-03, startup and deadline failure outputs need one explicit branch (low/medium).** Algorithm 1 says retain U=+infinity and report startup failure if no admissible fleet exists, then appears to continue to root initialization. H begins with a verified empty fleet, so this branch should occur only after invalid input/engineering/deadline failure, but the pseudocode should say return/stop rather than imply initialization of a finite-cutoff run. Similarly, distinguish a bounded finite operation that overruns the common deadline from a native request stopped by TimeLimit; the text already mentions external lifecycle enforcement, which should remain the operational boundary.

4. **S1-04, damaged math markup (low).** B.8 equation B3 contains `;qquad` rather than `;\\qquad`. Several appended sections use bare parentheses for intended inline math, and A.5.3/A.5.5 contain fragments such as `(k\\)` and `(i<j\\)`. The meaning is mostly recoverable, but this weakens the claim of a finished academic appendix and should be normalized.

5. **S1-05, old and current cutoff relevance should be explicit (low).** B.2/B.3 use `cutoff` in leaf eligibility and `outside-cutoff` in competitor exclusion, while old evidence retains its source cutoff and current requests use current own U. Explicitly distinguish selection's current U from source-cutoff metadata so a reimplementer cannot accidentally retain an obsolete competitor or discard an old complemented floor.

## Positive mathematical checks by reading

- The support handling lower bound uses all route pickups, not pickups restricted to W, and its inactive conditional-row branch has a valid nonnegative-coefficient deactivation argument.
- Ordered delivery support is justified by matching delivered units to earlier pickups; loaded return and external sources outside a small support do not invalidate it.
- H-spread and SP rows are asserted for a joint tight physical completion, not for every inflated auxiliary assignment.
- Non-strict cutoff complement is min(native floor, source cutoff); child union uses minimum, same-domain independent floors maximum.
- NEXT requeue priority, raw child LP values for AM, two-child replacement on infeasibility, and persistence of NEXT milestone across incumbent epochs are stated explicitly; these require source verification in Stage 2.

This stage is sealed before source access. Stage 2 will distinguish confirmed specification errors from intentional numerical or portability limits and will reread any repaired documents.
