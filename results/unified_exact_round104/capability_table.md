# Same-scope capability and objective retention

Historical rows are paid only as new expression diagnostics. Each row below
shares its original typed canonical matrix, columns, bounds and objective.
PASS is the actual R103-H production selection, not R102-J. The historical
LH values are closures within declared member tolerance, not rational optima.
F5 remains UNKNOWN. Its actual observed L0.0 scope is separately reoptimized;
its resource contract permits global source-row transfer, but its old LH is
not transferred as a bound of that narrower model.

| Scope | L0 RAW | Lpass H | LC ALL | LH qualification | ALL/ACTIVE/GROUPED rows | signed GROUPED−ALL |
|---|---:|---:|---:|---|---:|---:|
| F2 raw | 0.52862564946535495 | 0.52862564946463797 | 0.63800504040752337 | 0.63800504040449701 | 827/30/2 | -8.42199643358299e-11 |
| R98-C2 raw | 0.16123605049876005 | 0.16123605049876008 | 0.16123605049876008 | 0.16123605049876005 | 133/0/0 | -2.7755575615628914e-17 |
| F5 raw | 0.24416944802555995 | 0.24416944802753737 | 0.24416944802753754 | UNKNOWN / not established in this scope | 82/0/0 | -1.9775847626135601e-12 |
| F5 native L0.0 | 0.24420882282482045 | 0.24420882282465986 | 0.24420882282482045 | UNKNOWN / not established in this scope | 82/0/0 | 0 |

`reports_final02/objective_capability.csv` retains every expression, signed
difference, nonzero count and primal/dual residual. Tiny wrong-sign Pi are
explicitly repaired, strict negative Pi are retained without epsilon pruning.
The actual C++ compensated GROUPED2 result differs from ALL by
−6.023938015×10⁻¹⁰; the fleet1 result differs by −2.077199635×10⁻⁹.
Exact signed-bound compensation and native row readback passed; numerical
objective retention does not upgrade floating Pi into a rational certificate.
Python F2 GROUPED/FLEET are numerical expression diagnostics only: tiny
native-unsupported coefficients were not individually read back/compensated
for deletion. The independent review flags a nonzero-bound potential
deletion in GROUPED0, so its actual native-row validity is unqualified.
The C++ emitted GROUPED/FLEET rows have separate exact compensation and
actual native readback qualification. Node tests use the legal serialized
aggregate rows, not an assertion that the Python native LP contained them
coefficient-for-coefficient.

| Role | Actual sampled point | Node | Point objective | ALL reliable | ACTIVE reliable | GROUPED reliable |
|---|---|---:|---:|---:|---:|---:|
| F2 | first_root_relaxation | 0.0 | 0.60717996026446841 | 304 | 16 | 1 |
| F2 | latest_root_relaxation | 0.0 | 0.76858662573579561 | 9 | 0 | 0 |
| F2 | bounded_nonroot_relaxation | 1.0 | 0.77301023005469915 | 5 | 2 | 0 |
| F2 | bounded_nonroot_relaxation | 10.0 | 0.77591513635661113 | 29 | 2 | 0 |
| F2 | bounded_nonroot_relaxation | 100.0 | 0.81160940162565831 | 9 | 1 | 0 |
| R98-C2 | first_root_relaxation | 0.0 | 0.16123605049876003 | 0 | 0 | 0 |
| R98-C2 | latest_root_relaxation | 0.0 | 0.18875094776129178 | 0 | 0 | 0 |
| R98-C2 | bounded_nonroot_relaxation | 1.0 | 0.18874524284515182 | 0 | 0 | 0 |
| R98-C2 | bounded_nonroot_relaxation | 10.0 | 0.18923586131527187 | 0 | 0 | 0 |
| R98-C2 | bounded_nonroot_relaxation | 100.0 | 0.19052636623931793 | 0 | 0 | 0 |
| F5 | first_root_relaxation | 0.0 | 0.24420882282482045 | 0 | 0 | 0 |
| F5 | latest_root_relaxation | 0.0 | 0.28141416661991164 | 0 | 0 | 0 |

Reliability threshold is10× unchanged native FeasibilityTol=10⁻⁵ on the
actual admitted/scaled row. All12 full vectors satisfy their original scoped
matrix at its unchanged feasibility tolerance. The latest sampled root is
only the last observable root, never asserted to include every internal cut.
F5 has no positive-node sample in its180s window. A point objective/global LB
above old LH does not establish that native cuts imply the complete domain.
The old R103 “native” point came from J-SUBMIT; it is not used as original ENS
evidence here. The production candidate generates a fresh pool; its982/29
rows are separate from this historical827/30-row expression diagnosis.
