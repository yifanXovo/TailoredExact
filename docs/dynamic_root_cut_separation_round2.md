# Dynamic Root Cut Separation Round 2

The compact interval BC path now supports a true root probe loop:

1. write the fixed-interval compact model;
2. solve a root LP probe through CPLEX;
3. parse root variable values;
4. separate violated valid cuts;
5. rewrite the interval model with generated dynamic cuts;
6. solve the final MIP/BC certificate model.

Implemented dynamic families:

- support-duration incompatibility candidates;
- transfer compatibility rows;
- visit-final-inventory linking rows;
- objective-estimator cutoff row;
- singleton receiver-source-cover rows.

The interval smoke row
`results/gf_compact_bc_strengthening_round2/raw/dynamic_root_smoke.json`
generated six dynamic `visit_inventory_linking` rows. The V20 focused rows did
not show enough root violations for dynamic cuts to close the remaining
moderate leaves in this run.

Summary CSV:
`results/gf_compact_bc_strengthening_round2/dynamic_root_cut_summary.csv`.

