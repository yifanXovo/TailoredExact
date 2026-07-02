# Compact-BC Source Semantics V3

Fixed-interval `interval-cutoff-oracle` rows are leaf-solver rows and must report `compact_bc_called_this_row=true`. Parent `gcap-frontier` rows aggregate child `.auto_oracle.csv` and `interval_*.json` evidence into `compact_bc_called_any_child` without treating diagnostic rows as paper certificates.
