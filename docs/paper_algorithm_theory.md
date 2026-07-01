# Paper Algorithm Theory Index

The realigned paper theory is split into:

- `docs/paper_writing_module/01_problem_definition.md`;
- `docs/paper_writing_module/02_unified_algorithm.md`;
- `docs/paper_writing_module/03_global_optimality_theorem.md`;
- `docs/paper_writing_module/04_valid_relaxations_and_cuts.md`;
- `docs/paper_writing_module/05_bpc_fallback_theory_and_current_role.md`;
- `docs/paper_writing_module/06_interval_oracle_auxiliary_role.md`;
- `docs/paper_writing_module/07_large_v_scope_and_limitations.md`.

The central distinction is:

- `paper-gf-compact-bc`: active empirical paper-facing framework, using the
  Gini-frontier ledger plus compact fixed-interval branch-and-cut/cutoff
  certificates.
- `paper-gf-bpc-core`: unified GF + relaxation + exact BPC closure.  No
  route-mask enumeration or interval-oracle certificate evidence.  Retained for
  BPC theory and future implementation work.
- `paper-exact-portfolio`: auxiliary exact methods with separate labelling and
  audit.
- `CPLEX benchmark`: comparison only.
