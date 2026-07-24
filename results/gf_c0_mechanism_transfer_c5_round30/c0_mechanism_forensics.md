# C0 mechanism forensics

## Scope and identity

The audit reads 57 retained cold Gurobi C0/C1-equivalent runs from
Rounds 25 and 26, containing 1386 native leaf-processing events and
317 observed atomic splits.  Round 26 C1 is labelled `C0=C1`; its
independent variability is not treated as an algorithm change.  Telemetry
(time, Work, nodes) is descriptive and never used by a proposed C5 decision.

## Bound-value decomposition

- First processing contributes 44.4888993 summed leaf-bound gain
  and 43.3156144 immediately controlling global-bound gain using
  42683.8145 Work.
- Repeated same-leaf processing contributes 2.40885584 summed
  leaf-bound gain and 1.3793574 immediate global-bound gain
  using 69500.3337 Work.
- 307/517 second processings
  (59.4%) materially improve
  their leaf bound.
- 45/317 splits
  (14.2%) have an observed
  material first-child controlling-bound gain; the remainder are zero-value
  or unproved by the retained immediate-child evidence.
- 216 leaf-processing events close the leaf natively.  Independently
  verified incumbent improvement is not a material source in these retained
  external events (8 observed).

The attribution denominator is summed observed leaf/child gain
(46.9921105), not counterfactual runtime.  Direct split events inherit the
parent bound and therefore do not themselves create a lower bound; value comes
from subsequent child processing.

## Transfer conclusion

The dominant transferable mechanisms are valid partial native-MIP lower-bound
harvesting, parent-bound inheritance, exact atomic coverage, and best-bound
interleaving.  The hardware-dependent 30/60/... second allocation and
split-after-two-attempt rule explain when C0 stopped or split but are not
transferable.  Repeated processing often adds proof value, yet it also reruns
presolve/root work and cannot be used as a mathematical state merely because
it is the second call.
