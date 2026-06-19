# ExactEBRP reference bundle

This bundle is intended to be copied into `ExactEBRP/reference/` in the local repository.

Recommended usage:

1. Keep `Paper Draft 2.docx`, `ebrp_problem_model_spec.md`, `codex_upload_manifest.md`, and the latest `/goal` prompt in `ExactEBRP/reference/`.
2. Add the Python prototypes and JSON/TEX reports in this bundle as reference material only.
3. The production solver should be implemented in C++ under `ExactEBRP/`, using the old `Hybrid GA/` project for parser/generator/CPLEX baseline conventions.

Important reference files:

- `bpc_gini_cuts.py`: latest Python GF-RL-BPC prototype with subset-row cuts and co-route branching.
- `bpc_gini_frontier.py`: earlier route-load branch-price prototype.
- `milp_strong.py`: strengthened compact exact MILP prototype that certified one V12 sample.
- `gcap_exact.py`: Gini-cap MILP prototype.
- `gcap_benders.py`, `master_relax.py`: route-load oracle/master attempts.
- `ccbi_exact.py`, `box_exact.py`, `spatial_exact.py`: alternative exact reformulations that were less successful but useful as negative evidence.
- `gf_rl_bpc_cuts_report.tex`, `equity_brp_tailored_exact_interim_report.tex`, `bpc_implementation_report.tex`: mathematical/design notes.
- `*_results*.json`, `res_avg.json`: prior test summaries and a known certified solution on one V12 instance.
- `regen_candidate_V12_*.txt`: six quick regression samples in a simple text format.
- `codex_goal_prompt_exact_ebrp_v2.txt`: latest prompt adapted for a local C++ project with all files under `ExactEBRP/reference/`.
