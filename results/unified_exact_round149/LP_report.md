# Matched LP evidence

Exactly three base-D product-feedback optimizations and one scalar-only control were purchased. The complete saved R146 models, cutoffs, objectives, constants, variable domains, resource/support scope and all original rows were retained. Their saved qualified optima and points were reused without a new baseline Optimize. No old variable was fixed. These are three physical instances, not five independent instances; the old K20 joint/STOCK points are background only.

| Domain | Saved D optimum | PF optimum | Increment | Safe p lower | Safe beta | New rows/NZ |
|---|---:|---:|---:|---:|---:|---:|
| K20 base | .236010302342365 | .237043344713575 | .001033042371211 | .147656133333331 | .627556624469191 | 451/902 |
| K35 base | .204187028163866 | .206104958905020 | .001917930741154 | .161538478571428 | .605918126153288 | 539/1078 |
| RX20 base | .365004645621491 | .365603247853745 | .000598602232255 | .209859195562119 | .543194722527563 | 143/286 |

K35 scalar-only gives .204186705655193, a difference of -3.225086737e-7 from the saved D value. This is within the existing 1e-6 numerical quality standard and consistent with the exact redundancy argument. It is not a newly improving scalar inequality. No numerical pursuit of literal zero or baseline reoptimization was undertaken.

All four solves returned OPTIMAL, Seed0/Threads1, and passed the inherited residual/quality criteria. The result files retain all constraint/bound/dual/complementarity diagnostics, construction/readback/Native/outer costs, objective decomposition, matrix and point hashes, and actual submitted row counts. These are qualified floating LP optima, not exact rational optimality certificates. Exact arithmetic certifies the resource floor and coefficient direction only.

The independent review identified a nontrivial K35 numerical primal-dual diagnostic difference: PF reports primal .206104958905020 and diagnostic dual .205485913193, a difference about .000619046; scalar-only has about .001812609. Both pass the previously accepted quality tolerances, but these diagnostics should be read alongside the solver-reported optimum, never hidden behind an exact-bound claim. Even the PF diagnostic dual remains about .001298885 above the saved old primal .204187028164, so the direction of the K35 signal is clear. K20/RX20 differences are at floating-roundoff scale. See each `LP/*/result.json` for full precision and adverse reduced-cost diagnostics.

The actual old points satisfy the tighter scalar bound yet violate PF. New reoptimization improves all three objective values; this goes beyond saved-point separation. It does not establish MIP benefit. K35 supplies the clearest difficult-role optimization increment at small construction cost, which motivates one predeclared same-new-PE cap2400 D/PF pair after independent production admission. Its own beta must be reconstructed from each arm's paid own H; none of these historical betas is injected into a full arm.
