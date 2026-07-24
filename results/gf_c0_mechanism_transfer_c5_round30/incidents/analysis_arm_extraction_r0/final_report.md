# Round 30 final report

Round 30 completed 78 unique official processes
and materialized Stage 1/2/3/4 as
21/51/
25/10 rows.

The corrected Round 29 audit marks every C4 row lacking a compatible observed
global trace `auc_unavailable`; no endpoint pseudo-trajectory is used.

C0 forensics identify validity-gated partial native bounds, exact inherited
coverage, and best-bound interleaving as transferable. Fixed time quanta,
attempt counts, retry counts, and Work/node/solution controls remain
forbidden. The selected C5 uses `rho=0.01` and a
`GRB_CB_MIP_OBJBND` target equal to the complete child-disjunction bound.

All C5 structural exactness gates: **True**. All C5 trace gates:
**True**. False-certificate gate: **True**.

Against C4 on the 17-row primary matrix, C5 has 10 strict final-LB
wins and 0 observed common-window normalized proof-AUC wins among
17 AUC-eligible pairs.

Final classification: **exact_c0_mechanism_transfer_partial**.

S0/F0-CPLEX remains the stable accepted paper mainline. C0 remains an exact
but non-paper-compatible diagnostic teacher. C5 is not promoted automatically.
