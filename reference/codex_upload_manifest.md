# Recommended files to provide to Codex for the ExactEBRP task

## Must-have local repository content

1. The full repository root containing sibling directories:
   - `ExactEBRP/` as the new target project directory.
   - `Hybrid GA/` as the reference old implementation.

2. From `Hybrid GA/`, Codex must be able to read:
   - `Solver_Exact_CPLEX.cpp` and related headers/source files.
   - Any parser, instance, parameter, evaluator, route, and data-generation code.
   - `Hybrid GA/testdata/Smallnetwork2/` with existing samples.

## Must upload or include as reference documents

1. `Paper Draft 2.docx`.
2. `ebrp_problem_model_spec.md` generated in this conversation.
3. `codex_goal_prompt_exact_ebrp.txt` generated in this conversation.

## Useful prior prototype/reference files from this conversation

Upload these as a `reference/` folder, not as production code:

- `milp_strong.py` : strengthened compact exact prototype; got a certified optimum on one V12 M1 average instance.
- `gcap_exact.py` : fixed-Gini-cap exact subproblem prototype.
- `bpc_gini_frontier.py` : first route-load branch-price/frontier prototype.
- `bpc_gini_cuts.py` : latest GF-RL-BPC prototype with subset-row cuts and co-route branching.
- `gcap_benders.py` and `master_relax.py` : route-load oracle/master experiments.
- `ccbi_exact.py` and `box_exact.py` : negative/less successful exact formulations; useful to avoid repeating dead ends.
- `gf_rl_bpc_cuts_report.tex` : mathematical notes on the latest BPC design.
- `equity_brp_tailored_exact_interim_report.tex` : interim exact-method report.
- `root_mippricing_cuts_results_complete.json`, `bpc_test_results_updated.json`, `bpc_parallel_test_results.json`, `bpc_branch_probe.json`, `res_avg.json` : prior test results.

## Sample data from this conversation

Include these if possible for quick regression tests:

- `regen_candidate_V12_M1_average.txt`
- `regen_candidate_V12_M1_high.txt`
- `regen_candidate_V12_M1_low.txt`
- `regen_candidate_V12_M2_average.txt`
- `regen_candidate_V12_M2_high.txt`
- `regen_candidate_V12_M2_low.txt`

## What not to do

- Do not ask Codex to tune by changing the sample distributions.
- Do not ask Codex to reduce capacities, truck capacity, target inventories, or time windows to make the solver look fast.
- Do not accept a heuristic incumbent as exact.
- Do not rely only on root LP column generation as an optimality certificate for the integer problem.
