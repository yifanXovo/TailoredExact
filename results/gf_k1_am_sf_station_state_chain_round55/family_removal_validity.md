# Active-family removal validity

The 17 active F0-CLEAN families were classified before any live sparse arm was
selected.  Inventory conservation, routing/visit links, connectivity,
interval coverage, exact product definition, objective definition, required
linking, and certificate rows are not removal candidates.  Domain and closure
families are likewise part of the proved current formulation or its exact
scope and cannot be removed on an activity heuristic.

Six families are strengthening-only in the sense that removing them leaves a
valid exact base MIP: the objective lower estimator, penalty lower-bound row,
the four SP-product McCormick rows together with their auxiliary product,
the SP objective estimator, and the pair and triple support-duration covers.
That fact proves only validity after removal.  It does not satisfy the Round 55
entry gate, which additionally requires negligible contribution across
multiple roles, material matrix/LP cost, and a favorable isolated objective/
Work effect under a uniform removal.

The initial candidate freeze did not expose a stable family toggle and had no
completed family-resolved root-LP evidence meeting all four conditions.
Accordingly, no sparse arm entered the mandatory initial live pilot.  The
subsequent full offline removal diagnostics, completed before confirmation,
showed that the triple family alone contributes 216,919 rows, zero strict root
bounds, and a 0.8687645295438094 removal Work ratio over 27 frozen states.
Round 55's separately frozen controlled-development policy permits one
post-initial cut-management revision based on development evidence.  Revision
1 therefore introduces SF-R1 through a first-class uniform toggle and runs the
complete D1--D14 panel.  This is a controlled revision, not a retrospective
change to the initial sparse-candidate selection.  SF-R2 remains unopened.
